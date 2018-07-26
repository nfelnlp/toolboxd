import pandas as pd


def apply_sorting(df, flags):
    # All trivial flags
    for fl in reversed(list(flags)):
        # Descending (default)
        order = False
        if fl.endswith('_asc'):
            # Ascending
            order = True
            fl = fl[:-4]
        df = df.sort_values(fl, ascending=order)

    return df
