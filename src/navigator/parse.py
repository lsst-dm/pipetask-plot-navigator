import os
import re
from pathlib import Path
import hashlib

import pandas as pd
from tqdm import tqdm

# Globals
from .config import filters, types, category_path, plot_data_path


def parse_name(s):
    m = re.search("^(\w+-\w+)-(\S+).png$", s)
    if m:
        prefix, content = m.group(1), m.group(2)
    else:
        print(f"no match: {s}")
    filt = None
    for f in filters:
        if content.startswith(f):
            filt = f
            content = content[len(f) + 1 :]
    plot_type = None
    short_content = content
    for t in types:
        m = re.search(f"(.*)-{t}.*", content)
        if m:
            plot_type = t
            short_content = m.group(1)

    return prefix, content, short_content, plot_type, filt


def parse_prefix(prefix):
    """Returns datastyle (coadd/visit), visit/tract number, and whether compare or not
    """
    m = re.search("v(\d+)", prefix)
    if m:
        datastyle = "visit"
        number = int(m.group(1))
    m = re.search("t(\d+)", prefix)
    if m:
        datastyle = "coadd"
        number = int(m.group(1))

    compare = "compare" in prefix

    return datastyle, number, compare


def build_df(filenames):
    basenames = [os.path.basename(f) for f in filenames]

    prefix, content, short_content, plot_type, filts = zip(*[parse_name(s) for s in basenames])
    datastyle, number, compare = zip(*[parse_prefix(p) for p in prefix])

    df = pd.DataFrame(
        {
            "filename": filenames,
            "basename": basenames,
            "prefix": prefix,
            "content": content,
            "short_content": short_content,
            "filt": filts,
            "type": plot_type,
            "datastyle": datastyle,
            "number": number,
            "compare": compare,
        }
    )

    categories_df = pd.read_csv(category_path, index_col="name")

    missing_content = set(df.short_content.unique()) - set(categories_df.index)
    if len(missing_content) > 0:
        raise RuntimeError(f'Please add the following plot types to {category_path} and run again: {missing_content}')

    df["category"] = categories_df.loc[df.short_content, "category"].values

    # Fill in the filter field for those missing
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Imputing filter names for each row"):
        if row.filt is None:
            for filt in filters:
                if filt in row.filename:
                    df.loc[i, "filt"] = filt

    return df


def get_df(repo_path, clobber=False):
    if not repo_path:
        return None
    filenames = [str(f) for f in Path(repo_path).rglob('*.png')]
    if not filenames:
        raise ValueError(f'No plots found in {repo_path}')

    key = hashlib.md5(bytes(Path(repo_path).absolute())).hexdigest()
    store = pd.HDFStore(plot_data_path)

    if key not in store or clobber:
        df = build_df(filenames)
        store.put(f'{key}/plot_data', df)

    df = store.get(f'{key}/plot_data')
    store.close()
    return df

