    @property
    def _is_unique(self):
        return len(unique1d(self.asi8)) == len(self)

    # ------------------------------------------------------------------
    # Arithmetic Methods

    def _cmp_method(self, other, op):
        if self.ndim > 1 and getattr(other, "shape", None) == self.shape:
            # TODO: handle 2D-like listlikes
            return op(self.ravel(), other.ravel()).reshape(self.shape)

        try:
            other = self._validate_comparison_value(other)
        except InvalidComparison:
            return invalid_comparison(self, other, op)

        dtype = getattr(other, "dtype", None)
        if is_object_dtype(dtype):
            # We have to use comp_method_OBJECT_ARRAY instead of numpy
            #  comparison otherwise it would fail to raise when
            #  comparing tz-aware and tz-naive
            with np.errstate(all="ignore"):
                result = ops.comp_method_OBJECT_ARRAY(
                    op, np.asarray(self.astype(object)), other
                )
            return result

        other_vals = self._unbox(other)
        # GH#37462: comparison on i8 values is faster than M8/m8
        if isinstance(other_vals, np.ndarray) and other_vals.dtype.kind == "M":
            # For datetime64/timedelta64, use i8 view for faster comparison
            other_vals = other_vals.view("i8")
        result = op(self.asi8, other_vals)

        o_mask = isna(other)
        if self._hasnans | np.any(o_mask):
            nat_result = op is operator.ne
            result[self._isnan | o_mask] = nat_result

        return result
