import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import recall_score
from visualizer.analysis.base import ensure_directory

# Set the random generator seed
seed = 42

# Matplotlib settings
plt.style.use("classic")

# Seaborn settings
sns.set()
sns.set(font_scale=1.0)
sns.set_style({"font.family": "serif", "font.serif": ["Times New Roman"]})


def sensitivity_score(y_true, y_pred):
    return recall_score(y_true, y_pred)


def specificity_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp)


def binarize_proba(y_prob, decision_threshold):
    return (y_prob >= decision_threshold).astype("int")


def get_fi(model, f, k=10, sort=True):
    """
    Get feature importances

    This function gets the feature importances of an input <model> trained with the features
    <f> (feature names) and a label <y> (label name). It gets the first <k> features, which
    may or may not be sorted (according to <sort>).

    Parameters
    ----------

    model : obj
        tree-based object supporting <model>.feature_importances_ (e.g. XGBoost)

    f : list
        list with the feature names

    y : str
        str with name of the label (dependent variable: y)

    k : int, optional, default 10
        int value with number of important features to plot

    sort : bool, optional, default False
        boolean flag for plotting the sorted features

    Returns
    -------

    List of dicts with the features and their importances
    """

    # Extract the feature importance from the model
    features = list(zip(model.feature_importances_, f))

    # Get the list of sorted and trimmed feature importance
    features = sorted(features, reverse=True) if sort else features
    features = features[:k if k < len(features) else len(features)] if k else features

    # Return the feature importance
    return [
        {"feature": feature, "importance": round(float(importance), 6)}
        for importance, feature in features
    ]


def plot_fi(
        model,
        f,
        y,
        k=10,
        sort=False,
        ax=None,
        fig_show=True,
        save_as="tmp.pdf",
        fig_kwargs=None,
        bar_kwargs=None):
    """
    Plot feature importances

    This function plots the feature importances of an input <model> trained with the features
    <f> (feature names) and a label <y> (label name). It shows the first <k> features, which
    may or may not be sorted (according to <sort>). If <ax> is provided, new figure and axes
    are not created. The figure can be shown (according to <fig_show>) and stored locally
    (according to <save_as>). Additional figure settings are privuded in <fig_kwargs>.
    The bar-graph settings are provided in <bar_kwargs>.

    For more information about the used bar-graph function, see:
    https://seaborn.pydata.org/generated/seaborn.barplot.html

    Parameters
    ----------

    model : obj
        tree-based object supporting <model>.feature_importances_ (e.g. XGBoost)

    f : list
        list with the feature names

    y : str
        str with name of the label (dependent variable: y)

    k : int, optional, default 10
        int value with number of important features to plot

    sort : bool, optional, default False
        boolean flag for plotting the sorted features

    ax : matplotlib.axes, optional, default None
        axes object

    fig_show : bool, optional, default True
        boolean flag for figure showing

    save_as : str, optional, default "tmp.pdf"
        str with the full-path to store the figure into

    fig_kwargs : dict, optional, default None
        dict with additional figure settings

    bar_kwargs : dict, optional, default None
        dict with additional bar-graph settings

    Returns
    -------

    Tuple with axes object and the list of dicts with the fisrt <k> features and impotances
    """

    # Prepare the figure settings
    fig_kwargs = fig_kwargs if fig_kwargs else {
        "fig_size": (10, 10),
        "show_ticks": True,
        "ticks_rotation": 90,
        "x_label": "",
        "y_label": "",
        "title": f"feature importance: {y}"
    }

    # Prepare the bar-graph settings
    bar_kwargs = bar_kwargs if bar_kwargs else {"color": "#3b5b92", "edgecolor": "0.2"}

    # Get the feature importance(s)
    features = get_fi(model, f=f, k=k, sort=sort)

    # Create temporary DataFrame
    df_temp = pd.DataFrame(features)

    # Create figure if axes not inserted
    if not ax:
        fig, ax = plt.subplots(1, 1, figsize=fig_kwargs.get("fig_size"), sharex=False)

    # Create the bar-plot
    h = sns.barplot(x="feature", y="importance", data=df_temp, ax=ax, **bar_kwargs)

    # Set up the final adjustments
    h.set(xlabel=fig_kwargs.get("x_label"))
    h.set(ylabel=fig_kwargs.get("y_label"))
    h.set(title=fig_kwargs.get("title"))

    if fig_kwargs.get("show_ticks"):
        h.set_xticklabels(ax.get_xticklabels(), rotation=fig_kwargs.get("ticks_rotation"))
    else:
        h.set_xticklabels("")

        # Save the graph
    if save_as:
        ensure_directory(save_as)
        plt.savefig(save_as, bbox_inches="tight")

    # Show the graph
    if fig_show:
        plt.show()
    else:
        plt.close()

    return ax, features


def convert_disease_status_to_integers(value, zero_class=("HC", ), one_class=(), default_zero_class=("HC", )):
    """
    Convert disease status to machine-understandable number representation

    This function converts string-like disease status to a numerical representation that
    is feasible for the machine learning algorithms. It gives an option of defining our
    own sets of strings for zero and one classes (for now, it supports binary cls only).

    Parameters
    ----------

    value : str
        string-like disease status

    zero_class : zero class, optional, default ("HC", )
        tuple with the strings for the zero class

    one_class : one class, optional, default ()
        tuple with the strings for the one class

    default_zero_class : default zero class, optional, default ("HC", )
        tuple with the default strings for the zero class

    Returns
    -------

    Integer-like class value
    """

    # Validate the input arguments
    if not isinstance(value, (str, int)):
        raise TypeError(f"Unsupported type for the value: {type(value)}")
    if not isinstance(zero_class, (list, tuple, str)):
        raise TypeError(f"Unsupported type for the zero_class: {type(zero_class)}")
    if not isinstance(one_class, (list, tuple, str)):
        raise TypeError(f"Unsupported type for the one_class: {type(one_class)}")
    if isinstance(value, int):
        return value

    # Prepare the input arguments
    zero_class = zero_class if isinstance(zero_class, (list, tuple)) else [zero_class]
    one_class = one_class if isinstance(one_class, (list, tuple)) else [one_class]

    # Convert the disease status
    if all((zero_class, one_class)):
        if value in zero_class:
            return 0
        if value in one_class:
            return 1
        raise ValueError(f"Unknown class status '{value}'")
    if not any((zero_class, one_class)):
        return 0 if value in default_zero_class else 1
    if zero_class:
        return 0 if value in zero_class else 1
    if one_class:
        return 1 if value in one_class else 0
