import plotly.graph_objects as go
import plotly.offline as pyo


def get_violin_plot_subject_vs_norm_one_feature(subject, norm=None):
    """
    Gets the violin for the data (one feature) of a subject vs the norm.

    Info: https://plotly.com/python/violin/

    :param subject: data for a subject
    :type subject: dict
    :param norm: data for the norm
    :type norm: dict, optional
    :return: formatted HTML <div> element
    :rtype: str
    """

    # Prepare the data
    data = [
        go.Violin(
            y=subject['data'],
            name=subject.get('name', 'Subject'),
            box_visible=subject.get('box_visible', True),
            meanline_visible=subject.get('meanline_visible', True)
        )
    ]
    if norm:
        data.append(
            go.Violin(
                y=norm['data'],
                name=norm.get('name', 'Norm'),
                box_visible=norm.get('box_visible', True),
                meanline_visible=norm.get('meanline_visible', True)
            )
        )

    # Create the graph
    fig = go.Figure(data=data)

    # Return the graph
    return pyo.plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')
