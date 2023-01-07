import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.stats.multitest as multi
from itertools import combinations
from scipy.stats import ttest_ind, mannwhitneyu, wilcoxon
from visualizer.analysis.base import save_to_excel


def plot_box_violin(
        x,
        y,
        df,
        ax=None,
        fig_size=(8, 8),
        fig_show=True,
        save_as="figure.pdf",
        title=None,
        x_label=None,
        y_label=None,
        violinplot_kwargs=None,
        boxplot_kwargs=None,
        stripplot_kwargs=None):
    """
    Plot the box-violin graph

    This function plots the box-violin graph shoving the distribution of values
    for the categories. More specifically, the distribution of <x> over all of
    the categories of <y> in <df> is shown. This graph combines violin plot,
    box plot, and strip plot to improve the visual quality of the graph.

    Parameters
    ----------

    x : str
        Column-name for the categorical variable (x axis)

    y : str
        Column-name for the continuous variable (y axis)

    df : pandas.DataFrame
        Pandas DataFrame with the data for plotting

    ax : matplotlib.axes, optional, default None
        Axes to use for the plot (if no axes, a new figure is created)

    fig_size : tuple, optional, default (8, 8)
        Size of the figure

    fig_show : bool, optional, default True
        Figure showing switch

    save_as : str, optional, default "figure.pdf"
        Name of the saved figure (if None, saving skipped)

    title : str, optional, default None ("")
        Title of the plot

    x_label : str, optional, default None ("")
        Label of the x-axis

    y_label : str, optional, default None ("")
        Label of the y-axis

    violinplot_kwargs : dict, optional, default None
        Kwargs for violin plot

    boxplot_kwargs : dict, optional, default None
        Kwargs for box plot

    stripplot_kwargs : dict, optional, default None
        Kwargs for strip plot

    Returns
    -------

    None
    """

    # Get unique categories for categorical variable defines by y
    categories = list(df[x].unique())

    # Define color scheme
    color_names = ["purples", "greens", "pinks", "browns", "blues", "reds"]
    light_colors = ["#C39BD3", "#7DCEA0", "#FFC9EC", "#E5B699", "#85C1E9", "#D98880"]
    dark_colors = ["#884EA0", "#229954", "#FB84D1", "#B25116", "#2E86C1", "#A93226"]

    # Update color scheme according to the categories
    if len(categories) > len(color_names):
        multiplier = int(len(categories) / len(color_names)) + 1
        color_names = color_names * multiplier
        light_colors = light_colors * multiplier
        dark_colors = dark_colors * multiplier

    # Prepare the final color scheme
    colors = list(zip(color_names, light_colors, dark_colors))

    # Get the colors for the categories
    light_palette = {categories[i]: colors[i][1] for i in range(len(categories))}
    dark_palette = {categories[i]: colors[i][2] for i in range(len(categories))}

    # Default violinplot kwargs
    default_violinplot_kwargs = {
        "palette": light_palette,
        "alpha": 0.2,
        "width": 0.45,
        "inner": None,
        "linewidth": 0,
        "scale": "count",
        "saturation": 0.75,
        "hue_order": categories
    }

    # Default boxplot kwargs
    default_boxplot_kwargs = {
        "boxprops": {"edgecolor": "k", "linewidth": 0},
        "medianprops": {"color": "k", "linewidth": 2},
        "whiskerprops": {"color": "k", "linewidth": 2},
        "capprops": {"color": "k", "linewidth": 2},
        "palette": dark_palette,
        "width": 0.075,
        "fliersize": 0,
        "showcaps": True,
        "whis": 1.5,
        "notch": False,
        "hue_order": categories
    }

    # Default stripplot kwargs
    default_stripplot_kwargs = {
        "palette": light_palette,
        "linewidth": 0,
        "size": 8,
        "alpha": 0.2,
        "split": True,
        "jitter": True,
        "hue_order": categories
    }

    # Prepare kwargs for each plot type
    violinplot_kwargs = violinplot_kwargs if violinplot_kwargs else default_violinplot_kwargs
    boxplot_kwargs = boxplot_kwargs if boxplot_kwargs else default_boxplot_kwargs
    stripplot_kwargs = stripplot_kwargs if stripplot_kwargs else default_stripplot_kwargs

    # Create the figure and axes if necessary
    if not ax:
        fig = plt.figure(figsize=fig_size if fig_size else (8, 8))
        ax = fig.add_subplot(1, 1, 1)

    # Plot the graphs
    sns.violinplot(x=x, y=y, data=df, ax=ax, **violinplot_kwargs)
    sns.stripplot(x=x, y=y, data=df, ax=ax, **stripplot_kwargs)
    sns.boxplot(x=x, y=y, data=df, ax=ax, **boxplot_kwargs)

    # Get feature values for the categories
    observations = [df[df[x] == c] for c in categories]

    # Get values for pairs of the categories
    testing_combinations = combinations(range(len(observations)), 2)

    # Prepare the visualization counter
    count_lines = 0

    # Quantify and visualize the difference between the categories
    for combination in testing_combinations:

        # Get the feature values
        a = observations[combination[0]][y].values
        b = observations[combination[1]][y].values

        # Compute Mann-Whitney U-test
        _, p = mannwhitneyu(a, b)

        # Depict the p-value
        if p <= 0.001:
            p_str = "***"
        elif p <= 0.01:
            p_str = "**"
        elif p <= 0.05:
            p_str = "*"
        else:
            p_str = ""

        # Get the axes limits
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # Add the visualization of the p-value
        if p <= 0.05:
            count_lines += 1

            partition = 0.05 * (y_max - y_min)

            y_line_pos = y_max - (count_lines * partition)
            x_line_min = combination[0]
            x_line_max = combination[1]

            ax.hlines(y_line_pos, x_line_min, x_line_max, lw=2.5, color="k")

            x_pos_text = (combination[1] + combination[0]) / 2
            y_pos_text = y_line_pos - partition * 7 / 4
            plt.text(x_pos_text, y_pos_text, p_str, horizontalalignment="center", fontsize=24)

    for c in categories:
        y_pos = np.median(df[df[x] == c][y].values)
        ax.hlines(y_pos, x_min, x_max, linestyle="--", linewidth=2.0, color=dark_palette.get(c))

    # Apply additional adjustments
    plt.setp(ax.collections, alpha=0.65)

    ax.set_title(title if title else "")
    ax.set_xlabel(x_label if x_label else "")
    ax.set_ylabel(y_label if y_label else "")

    ax.yaxis.grid(True)
    ax.xaxis.grid(True)

    # Store the figure
    if save_as:
        plt.savefig(save_as)

    # Show the graph (if enabled)
    if fig_show:
        plt.show()


def test_hypothesis(x, y, test_type="ttest", supported_tests=("ttest", "mann_whitney", "wilcoxon")):
    """
    Test the hypothesis

    This function test the hypothesis between <x> and <y>. The hypothesis test function
    is chosen using the mapping of the <supported_types> and <test_type>. The function
    supports three types of hypothesis tests: ("ttest", "mann_whitney", "wilcoxon").

    Parameters
    ----------

    x : numpy ndarray
        numpy ndarray with the data

    y : numpy ndarray
        numpy ndarray with the data

    test_type : str, optional, default "ttest"
        str with the hypothesis test type

    supported_tests : iterable, optional, default ("ttest", "mann_whitney", "wilcoxon")
        iterable with the supported hypothesis test types

    Returns
    -------

    test results: h, p
    """

    # Prepare the mapping
    mapping = {"ttest": ttest_ind, "mann_whitney": mannwhitneyu, "wilcoxon": wilcoxon}

    # Test the hypothesis
    if not test_type in supported_tests:
        raise ValueError(f"Test type {test_type} is unsupported. Supported ones: {supported_tests}")
    return mapping[test_type.lower()](x, y)


def tabulate_hypothesis_test(
        df_feat,
        disease_status,
        sel_feat=None,
        alpha=0.05,
        adj_method="fdr_bh",
        save_as="tmp.xlsx"):
    """
    Tabulate the hypothesis testing

    This function tabulates the hypothesis test between the features in <df_feat> pandas
    DataFrame for healthy constrols and patients with PD. It assummesthat <df> has the
    following structure: rows: observations, columns: features. Names of the observations
    are set as the index. The function supports three types of hypothesis tests ("ttest",
    "mann_whitney", "wilcoxon"). The p-values are also adjusted using <adj_method> with
    the threshold of <alpha>. Finally, hypothesis test values between all features for
    the two subject groups.

    For more information about the p-values adjustment, see:
    www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

    Parameters
    ----------

    df_feat : pandas DataFrame
        pandas DataFrame with the handwriting features

    disease_status : list of ints
        list with the disease status

    sel_feat : iterable, optional, default None
        iterable with the names (column-names) of the handwriting features to analyse

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

    # Filter the features
    df_feat = df_feat[sel_feat] if sel_feat else df_feat

    # Prepare the hypothesis test types to use
    test_types = ("mann_whitney",)

    # Prepare the results table
    results = []

    for feat in df_feat:

        # Prepare the dictionary of test results
        tests = {"feature": feat}

        # Get the data for both subject groups
        feat_data = df_feat[feat]
        x = [float(v) for v, status in zip(feat_data, disease_status) if status == 0]
        y = [float(v) for v, status in zip(feat_data, disease_status) if status == 1]

        if any((all(not x_ > 0. for x_ in x), all(not y_ > 0. for y_ in y))):
            tests[f"healthy (median)"] = np.nan
            tests[f"healthy (iqr)"] = np.nan
            tests[f"diseased (median)"] = np.nan
            tests[f"diseased (iqr)"] = np.nan
            for test in test_types:
                tests[f"h ({test})"] = np.nan
                tests[f"p ({test})"] = np.nan
        else:

            # Prepare the data for the subject groups
            x = np.array(x)
            y = np.array(y)

            # Add basic statistics
            tests[f"healthy (median)"] = np.median(x)
            tests[f"healthy (iqr)"] = np.subtract(*np.percentile(x, [75, 25]))
            tests[f"diseased (median)"] = np.median(y)
            tests[f"diseased (iqr)"] = np.subtract(*np.percentile(y, [75, 25]))

            # Test the hypotheses
            for test in test_types:
                h, p = test_hypothesis(x, y, test_type=test)
                tests[f"h ({test})"] = round(float(h), 4)
                tests[f"p ({test})"] = round(float(p), 4)

        # Append to the results
        results.append(tests)

    # Convert the results into the pandas DataFrame
    results = pd.DataFrame(results)

    # Adjust the p-values
    for test in test_types:
        p_original = results[f"p ({test})"].values
        p_adjusted = multi.multipletests(p_original, alpha=alpha, method=adj_method, is_sorted=False)
        results[f"p adj ({test})"] = p_adjusted[1]

    # Save the DataFrame with the hypothesis tests
    save_to_excel(results, output_path=save_as, index=False)

    # Return the resulting table
    return results
