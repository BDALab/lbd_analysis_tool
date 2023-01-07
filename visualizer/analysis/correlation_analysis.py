import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.stats.multitest as multi
from scipy.stats.stats import pearsonr, spearmanr, kendalltau
from visualizer.analysis.base import ensure_directory, save_to_excel_multi


def plot_heat_map(df, save_as="tmp.pdf", kwargs=None):
    """
    Plot the heatmap

    This function plots the heatmap of the cross-correlation among the columns of an input
    DataFrame <df>. It assumes that <df> has the following structure: rows: observations,
    columns: features. Names of the observations are set as the index. It stores the graph
    as <save_as>. The heatmap's properties are defined via the optional arguments. For
    more information, see: https://seaborn.pydata.org/generated/seaborn.heatmap.html

    Parameters
    ----------

    df : pandas DataFrame
        pandas DataFrame (rows=observations, cols=features), index=observation names

    save_as : str, optional, default "tmp.xlsx"
        str with the full-path to store the heatmap into

    ...
    <seaborn.heatmap> kwargs, defaults (to be adjusted in each case):
    ...

    {
        "cmap": sns.diverging_palette(220, 10, as_cmap=True),
        "cbar_kws": {"ticks": np.arange(-1.0, +1.2, 0.2), "shrink": 0.733},
        "annot": True,
        "annot_kws": {"size": 10},
        "fmt": ".1f",
        "vmin": -1,
        "vmax": +1,
        "center": 0,
        "square": True,
        "linewidths": 0.5
    }

    Returns
    -------

    Figure and the axes
    """

    # Prepare the seaborn.heatmap kwargs
    kwargs = kwargs if kwargs else {
        "cmap": sns.diverging_palette(220, 10, as_cmap=True),
        "cbar": False,
        "cbar_kws": {"ticks": np.arange(-1.0, +1.2, 0.2), "shrink": 0.733},
        "annot": True,
        "annot_kws": {"size": 10},
        "fmt": ".1f",
        "vmin": -1,
        "vmax": +1,
        "center": 0,
        "square": True,
        "linewidths": 0.5
    }

    # Prepare the figure and the axes
    fig, ax = plt.subplots(figsize=(25, 25))

    # Compute the cross-correlation among the columns
    corr = df.corr()

    # Create the heatmap
    sns.heatmap(corr, ax=ax, **kwargs)

    # Adjust the plot's ticks and labels
    x_ticks = np.arange(len(corr.columns)) + 0.5
    y_ticks = np.arange(len(corr.columns)) + 0.5
    plt.xticks(x_ticks, corr.columns, fontname="Times New Roman", fontsize=11)
    plt.yticks(y_ticks, corr.columns, fontname="Times New Roman", fontsize=11)

    # Adjust the y-lim (solves the issue of cutting-off the top/bottom of the graph)
    ax.set_ylim(len(corr.columns) + 0.0, -0.0)

    # Rotate the x-ticks vertically
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Adjust the layout
    plt.tight_layout()

    # Save the graph
    ensure_directory(save_as)
    plt.savefig(save_as, bbox_inches="tight")

    # Show the graph
    plt.show()

    return fig, ax


def compute_correlation(x, y, corr_type="spearman", supported_types=("pearson", "spearman", "kendall")):
    """
    Compute the correlation

    This function computes the correlation between <x> and <y>. The correlation function
    is chosen using the mapping of the <supported_types> and <corr_type>. The function
    supports three types of correlation: ("pearson", "spearman", "kendall").

    Parameters
    ----------

    x : numpy ndarray
        numpy ndarray with the data

    y : numpy ndarray
        numpy ndarray with the data

    corr_type : str, optional, default "spearman"
        str with the correlation type

    supported_types : iterable, optional, default ("pearson", "spearman", "kendall")
        iterable with the supported correlation types

    Returns
    -------

    Correlation results: r, p
    """

    # Prepare the mapping
    mapping = {"pearson": pearsonr, "spearman": spearmanr, "kendall": kendalltau}

    # Compute the correlation
    if not corr_type in supported_types:
        raise ValueError(f"Corr. type {corr_type} is unsupported. Supported ones: {supported_types}")
    return mapping[corr_type.lower()](x, y)


def tabulate_correlation(
        df_feat,
        df_clin,
        sel_feat=None,
        sel_clin=None,
        alpha=0.05,
        adj_method="fdr_bh",
        save_as="tmp.xlsx"):
    """
    Tabulate the correlation

    This function tabulates the correlation between the features in <df_feat>* and clinical
    rating scales in <df_clin>* pandas DataFrames. It assummesthat <df> has the following
    structure: rows: observations, columns: features/clinical rating scales. Names of the
    observations are set as the index. The function supports three types of correlation:
    ("pearson", "spearman", "kendall"). The p-values are also adjusted using <adj_method>
    with the threshold of <alpha>. Finally, correlation between all features in <df_feat>
    and each column in <df_clin> is stored in a separate sheet in the excel file. The
    path to the file is set by <save_as>.

    *specific features can be set in <sel_feat> (if not, all features are used)
    *specific clinical rating scales can be set in <sel_clin> (if not, all scales are used)

    For more information about the p-values adjustment, see:
    www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

    Parameters
    ----------

    df_feat : pandas DataFrame
        pandas DataFrame with the handwriting features

    df_clin : pandas DataFrame
        pandas DataFrame with the clinical data

    sel_feat : iterable, optional, default None
        iterable with the names (column-names) of the handwriting features to analyse

    sel_feat : iterable, optional, default None
        iterable with the names (column-names) of the clinical rating scales to analyse

    alpha : int, optional, default 0.05
        int value with family-wise error rate

    adj_method : str, optional, default "fdr_bh"
        float value with p-values adjustment method to use

    save_as : str, optional, default "tmp.xlsx"
        str with the full-path to store the table with the results into

    Returns
    -------

    Dictionary with the result tables
    """

    # Filter the features and the clinical data
    df_feat = df_feat[sel_feat] if sel_feat else df_feat
    df_clin = df_clin[sel_clin] if sel_clin else df_clin

    # Prepare the correlation types to use
    corr_types = ("pearson", "spearman", "kendall")

    # Prepare a dict with tables to be created
    tables = {}

    # Compute the correlation for all clinical scales
    for clin in df_clin:

        # Prepare the results table
        results = []

        for feat in df_feat:

            # Get the data
            clin_data = df_clin[clin]
            feat_data = df_feat[feat]

            # Prepare the dictionary of correlations
            correlations = {"feature": feat}

            # Compute the correlation
            for corr in corr_types:
                r, p = compute_correlation(feat_data, clin_data, corr_type=corr)
                correlations[f"r ({corr})"] = round(float(r), 4)
                correlations[f"p ({corr})"] = round(float(p), 4)

            # Append to the results
            results.append(correlations)

        # Convert the results into the pandas DataFrame
        table = pd.DataFrame(results)
        tables[clin] = table

        # Adjust the p-values
        for corr in corr_types:
            p_original = table[f"p ({corr})"].values.copy()
            p_adjusted = multi.multipletests(p_original, alpha=alpha, method=adj_method, is_sorted=False)
            table[f"p adj ({corr})"] = p_adjusted[1]

    # Save the DataFrame with the correlations for the analysed clinical scale
    sheets = tables.keys()
    result = tables.values()
    save_to_excel_multi(result, sheets, output_path=save_as, index=False)

    # Return the resulting tables
    return tables


def starify_pval(pval):
    """
    Starify p-value

    This function starifies the p-value using the specific set of significance levels
    (thresholds) according to the following formula:
        *   <pval> < 0.050
        **  <pval> < 0.010
        *** <pval> < 0.001

    Parameters
    ----------

    pval : float
        p-value

    Returns
    -------

    starified string
    """
    if pval > 0.05:
        return ""
    else:
        if pval <= 0.001:
            return "***"
        if pval <= 0.01:
            return "**"
        if pval <= 0.05:
            return "*"


def plot_correlation(
        df_feat,
        df_clin,
        sel_feat=None,
        sel_clin=None,
        corr_type="spearman",
        threshold=0.05,
        fig_save_dir=""):
    """
    Visualize the correlation

    This function tabulates the correlation between the features in <df_feat>* and clinical
    rating scales in <df_clin>* pandas DataFrames. It assummesthat <df> has the following
    structure: rows: observations, columns: features/clinical rating scales. Names of the
    observations are set as the index. The function supports three types of correlation:
    ("pearson", "spearman", "kendall"). The p-values are also adjusted using <adj_method>
    with the threshold of <alpha>. Finally, correlation between all features in <df_feat>
    and each column in <df_clin> is stored in a separate sheet in the excel file. The
    path to the file is set by <save_as>.

    *specific features can be set in <sel_feat> (if not, all features are used)
    *specific clinical rating scales can be set in <sel_clin> (if not, all scales are used)

    For more information about the p-values adjustment, see:
    www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

    Parameters
    ----------

    df_feat : pandas DataFrame
        pandas DataFrame with the handwriting features

    df_clin : pandas DataFrame
        pandas DataFrame with the clinical data

    sel_feat : iterable, optional, default None
        iterable with the names (column-names) of the handwriting features to analyse

    sel_clin : iterable, optional, default None
        iterable with the names (column-names) of the clinical rating scales to analyse

    corr_type : str, optional, default "spearman"
        specific correlation type to use

    threshold : float, optional, default 0.05
        p-values threshold (significance level)

    fig_save_dir : str, optional, default ""
        str with the path to the directory to store the distribution plots into
    """

    # Filter the features and the clinical data
    df_feat = df_feat[sel_feat] if sel_feat else df_feat
    df_clin = df_clin[sel_clin] if sel_clin else df_clin

    # Prepare the correlation types to use
    corr_type = corr_type if corr_type else "spearman"

    # Prepare the figure and the axes
    fig, ax = plt.subplots(figsize=(10, 10))

    # Visualize the correlation for all clinical scales
    for clin in df_clin:
        for feat in df_feat:

            # Get the data
            clin_data = df_clin[clin]
            feat_data = df_feat[feat]

            # Compute the correlation
            r, p = compute_correlation(feat_data, clin_data, corr_type=corr_type)

            # Create the joint-plot
            h = sns.regplot(feat_data, clin_data, ci=95, truncate=False)

            # Set up the final adjustments
            stars = starify_pval(p)
            plt.title(r"$\rho = {:.4}$, $p = {:.4}{}$".format(r, p, f"({stars})" if stars else ""))
            plt.tight_layout()

            # Save the graph
            save_fig_as = f"{os.path.join(fig_save_dir, clin, feat)}.pdf"
            ensure_directory(save_fig_as)
            plt.savefig(save_fig_as, bbox_inches="tight")

            # Clear the figure after each iteration
            plt.close()
            plt.clf()
