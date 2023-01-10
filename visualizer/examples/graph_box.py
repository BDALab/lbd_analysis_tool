import plotly.graph_objects as go
import plotly.offline as pyo


def get_box_plot_subject_vs_norm_one_feature(subject, norm=None):
    """
    Gets the boxplot for the data (one feature) of a subject vs the norm.

    Info: https://plotly.com/python/box-plots/

    :param subject: data for a subject
    :type subject: dict
    :param norm: data for the norm
    :type norm: dict, optional
    :return: formatted HTML <div> element
    :rtype: str
    """

    # Prepare the data
    data = [
        go.Box(
            y=subject['data'],
            name=subject.get('name', 'Subject'),
            marker_color=subject.get('marker_color', 'darkblue'),
            boxmean=subject.get('boxmean', True)
        )
    ]
    if norm:
        data.append(
            go.Box(
                y=norm['data'],
                name=norm.get('name', 'Norm'),
                marker_color=norm.get('marker_color', 'royalblue'),
                boxmean=norm.get('boxmean', True)
            )
        )

    # Create the graph
    fig = go.Figure(data=data)

    # Return the graph
    return pyo.plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')
