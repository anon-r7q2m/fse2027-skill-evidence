# Exact source-method excerpts; globals and class bases are supplied by replay.py.

def compile_json_path(key_transforms, include_root=True, allow_array_index=True):
    path = ["$"] if include_root else []
    for key_transform in key_transforms:
        try:
            num = int(key_transform)
        except (ValueError, TypeError):  # non-integer or non-convertible
            path.append(".")
            path.append(json.dumps(key_transform))
        else:
            if allow_array_index:
                path.append("[%s]" % num)
            else:
                # Treat numeric-looking keys as object keys (quoted) when array
                # index interpretation is not allowed.
                path.append(".")
                path.append(json.dumps(key_transform))
    return "".join(path)


class KeyTransform(Transform):

    def __init__(self, key_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_name = str(key_name)


    def preprocess_lhs(self, compiler, connection):
        key_transforms = [self.key_name]
        previous = self.lhs
        while isinstance(previous, KeyTransform):
            key_transforms.insert(0, previous.key_name)
            previous = previous.lhs
        lhs, params = compiler.compile(previous)
        if connection.vendor == "oracle":
            # Escape string-formatting.
            key_transforms = [key.replace("%", "%%") for key in key_transforms]
        return lhs, params, key_transforms


    def as_mysql(self, compiler, connection):
        lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
        json_path = compile_json_path(key_transforms)
        return "JSON_EXTRACT(%s, %%s)" % lhs, tuple(params) + (json_path,)


class HasKeyLookup(PostgresOperatorLookup):

    logical_operator = None


    def as_sql(self, compiler, connection, template=None):
        # Process JSON path from the left-hand side.
        if isinstance(self.lhs, KeyTransform):
            lhs, lhs_params, lhs_key_transforms = self.lhs.preprocess_lhs(
                compiler, connection
            )
            lhs_json_path = compile_json_path(lhs_key_transforms)
        else:
            lhs, lhs_params = self.process_lhs(compiler, connection)
            lhs_json_path = "$"
        sql = template % lhs
        # Process JSON path from the right-hand side.
        rhs = self.rhs
        rhs_params = []
        if not isinstance(rhs, (list, tuple)):
            rhs = [rhs]
        for key in rhs:
            if isinstance(key, KeyTransform):
                *_, rhs_key_transforms = key.preprocess_lhs(compiler, connection)
                rhs_path = compile_json_path(rhs_key_transforms, include_root=False)
            else:
                rhs_key_transforms = [key]
                # On SQLite, MySQL and Oracle, numeric-looking object keys
                # should be treated as quoted object keys, not array indices.
                if connection.vendor in ("sqlite", "mysql", "oracle"):
                    rhs_path = compile_json_path(
                        rhs_key_transforms, include_root=False, allow_array_index=False
                    )
                else:
                    rhs_path = compile_json_path(rhs_key_transforms, include_root=False)
            rhs_params.append("%s%s" % (lhs_json_path, rhs_path))
        # Add condition for each key.
        if self.logical_operator:
            sql = "(%s)" % self.logical_operator.join([sql] * len(rhs_params))
        return sql, tuple(lhs_params) + tuple(rhs_params)


    def as_mysql(self, compiler, connection):
        return self.as_sql(
            compiler, connection, template="JSON_CONTAINS_PATH(%s, 'one', %%s)"
        )

