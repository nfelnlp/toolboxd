import pandas as pd


def split_up_entry(df, target):
    target_items = row[target].apply(list)
    print(target_items)
    input("...")
    if len(target_items) > 1:
        for item in target_items:
            df.append(df.loc[df[target] == item], ignore_index=True)
    return df


def apply_sorting(df, flags):
    # All trivial flags
    for fl in reversed(list(flags)):
        if fl.startswith('sum_'):
            target = fl.split('_')[-1]
            df.apply(split_up_entry, target)

            #print(df.groupby(target)["nrating"].apply(list))
            input("...")

        # Descending (default)
        order = False
        if fl.endswith('_asc'):
            # Ascending
            order = True
            fl = fl[:-4]
        df = df.sort_values(fl, ascending=order)

    return df
