import plotly.graph_objects as go
import plotly.offline as pyo


def get_radar_plot_subject_vs_norm_multiple_features(subject, norm=None, feature_names=None):
    """
    Gets the radar plot for the data (multiple features) of a subject vs the norm.

    Info: https://plotly.com/python/radar-chart/

    :param subject: data for a subject
    :type subject: dict
    :param norm: data for the norm
    :type norm: dict, optional
    :param feature_names: feature names
    :type feature_names: list, optional
    :return: formatted HTML <div> element
    :rtype: str
    """

    # Prepare the feature names
    feature_names = feature_names if feature_names else [f'feature {i + 1}' for i in range(len(subject["data"]))]

    #  Prepare the data
    data = [
        go.Scatterpolar(
            r=subject['data'],
            theta=feature_names,
            fill=subject.get('fill', 'toself'),
            name=subject.get('name', 'Subject')
        )
    ]
    if norm:
        data.append(
            go.Scatterpolar(
                r=norm['data'],
                theta=feature_names,
                fill=norm.get('fill', 'toself'),
                name=norm.get('name', 'Norm')
            )
        )

    # Prepare the layout
    layout = go.Layout(
        title=go.layout.Title(text=''),
        polar={'radialaxis': {'visible': True}},
        showlegend=True
    )

    # Create the graph
    fig = go.Figure(data=data, layout=layout)

    # Return the graph
    return pyo.plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')
