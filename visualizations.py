import altair as alt
from utils import get_country_sort_order

def make_main_strip_plot(df_to_chart, hidden_tiers=None, min_rating=None, league_to_highlight=None, show_median=True):

    # extract unique hex code values assigned to each league
    color_map = df_to_chart[['Country|Tier', 'Hex Color']].set_index('Country|Tier')['Hex Color'].to_dict()

    # combined key used for applying colors
    df_to_chart["country_tier"] = df_to_chart["Country"] + "|" + df_to_chart["League Tier"]

    # label for legend
    df_to_chart["country_league_label"] = df_to_chart["Country"] + " - " + df_to_chart["League"]

    # conditional mark opacity
    if league_to_highlight is not None:
        df_to_chart['ShowDatum'] = df_to_chart['League'] == league_to_highlight
    else:
        df_to_chart['ShowDatum'] = df_to_chart['Rating'] >= (min_rating if min_rating is not None else 0)

    # conditional median opacity
    if show_median:
        median_line_opacity = .45
    else:
        median_line_opacity = 0

    # set y range for ease of use (adds a bit of padding)
    y_min = df_to_chart["Rating"].min() - 5
    y_max = 104

    # optional hidden tiers functionality (can hide divisions - mapped in data as Tiers)
    hidden_tiers = hidden_tiers or []
    tier_filter = " && ".join([f"datum['League Tier'] != '{t}'" for t in hidden_tiers]) or "true"

    # Get only the visible combinations and create sorted order for legend
    visible_combos = (
        df_to_chart[df_to_chart["League Tier"].isin([t for t in ["Tier 1", "Tier 2", "Tier 3"] if t not in hidden_tiers])]
        [["Country", "League", "League Tier", "country_tier", "country_league_label"]]
        .drop_duplicates()
    )

    # sort by country (using country order) then by tier
    country_order = get_country_sort_order(df_to_chart)
    tier_order_int = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3}
    visible_combos["country_rank"] = visible_combos["Country"].map({c: i for i, c in enumerate(country_order)})
    visible_combos["tier_rank"] = visible_combos["League Tier"].map(tier_order_int)
    visible_combos = visible_combos.sort_values(["country_rank", "tier_rank"])

    # create mapping from country_tier to country_league_label for legend
    legend_order = visible_combos["country_league_label"].tolist()
    legend_domain = visible_combos["country_tier"].tolist()
    legend_range = [color_map[ct] for ct in legend_domain]

    main = (
        alt.Chart(df_to_chart)
        .transform_filter(tier_filter)
    )

    # strip plot
    points = (
        main
        .mark_circle(
            size=100,
            opacity=0.9
        )
        .encode(
            x=alt.X(
                "Country:N",
                sort=country_order,
                scale=alt.Scale(domain=country_order),
                axis=alt.Axis(titleColor='White', labelColor='White', domain=False),
            ),
            y=alt.Y(
                "Rating:Q",
                scale=alt.Scale(domain=[y_min, y_max], nice=False),
                axis=alt.Axis(
                    domain=False,
                    titleColor='White',
                    labelColor='White',
                    gridOpacity=.5,
                    gridColor='lightgray',
                    gridDash=[2,2],
                ),
            ),
            xOffset="jitter:Q",
            color=alt.Color(
                "country_league_label:N",
                scale=alt.Scale(
                    domain=legend_order,
                    range=legend_range,
                ),
                legend=alt.Legend(
                    title="Country - League",
                    titleColor='White',
                    labelColor='White',
                    orient='right',
                    labelLimit=300,
                ),
            ),
            opacity=alt.condition(
                alt.datum.ShowDatum,
                alt.value(0.9),
                alt.value(0.3)
            ),
        )
        .transform_calculate(
            jitter="clamp(0.02 * sqrt(-2*log(random()))*cos(2*PI*random()), -0.3, 0.3)"
        )
    )

    # create agg data for median
    tiers_to_display_median = df_to_chart[df_to_chart["League Tier"].isin([t for t in ["Tier 1", "Tier 2", "Tier 3"] if t not in hidden_tiers])]
    median_data = (
        tiers_to_display_median.groupby(["Country","country_tier","country_league_label"], as_index=False)["League Median Rating"].mean()
    )

    # median lines
    median_lines = (
        alt.Chart(median_data)
        .mark_tick(
            size=75,
            thickness=3,
            opacity=median_line_opacity
        )
        .encode(
            x=alt.X(
                "Country:N",
                sort=country_order,
                scale=alt.Scale(domain=country_order),
            ),
            x2=alt.X2("Country:N"),
            y="League Median Rating:Q",
            color=alt.Color(
                "country_league_label:N",
                scale=alt.Scale(
                    domain=legend_order,
                    range=legend_range,
                ),
                legend=None,
            ),
        )
    )

    return (
        (points + median_lines)
        .properties(width='container')
        .configure(background='#000000')
        .configure_view(stroke=None)
        .resolve_scale(xOffset='independent')
    )


def make_interactive_dashboard(df_to_chart, hidden_tiers=None, show_median=False):

    # extract unique hex code values assigned to each league
    color_map = df_to_chart[['Country|Tier', 'Hex Color']].set_index('Country|Tier')['Hex Color'].to_dict()

    # combined key used for applying colors
    df_to_chart["country_tier"] = df_to_chart["Country"] + "|" + df_to_chart["League Tier"]

    # label for legend
    df_to_chart["country_league_label"] = df_to_chart["Country"] + " - " + df_to_chart["League"]

    # conditional median opacity
    if show_median:
        median_line_opacity = .45
    else:
        median_line_opacity = 0

    # set y range for ease of use (adds a bit of padding)
    y_min = df_to_chart["Rating"].min() - 5
    y_max = 104

    # optional hidden tiers functionality (can hide divisions - mapped in data as Tiers)
    hidden_tiers = hidden_tiers or []
    tier_filter = " && ".join([f"datum['League Tier'] != '{t}'" for t in hidden_tiers]) or "true"

    # get only the visible combinations and create sorted order for legend
    visible_combos = (
        df_to_chart[df_to_chart["League Tier"].isin([t for t in ["Tier 1", "Tier 2", "Tier 3"] if t not in hidden_tiers])]
        [["Country", "League", "League Tier", "country_tier", "country_league_label"]]
        .drop_duplicates()
    )

    # sort by country (using country order) then by tier
    country_order = get_country_sort_order(df_to_chart)
    tier_order_map = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3}
    visible_combos["country_rank"] = visible_combos["Country"].map({c: i for i, c in enumerate(country_order)})
    visible_combos["tier_rank"] = visible_combos["League Tier"].map(tier_order_map)
    visible_combos = visible_combos.sort_values(["country_rank", "tier_rank"])

    # create mapping from country_tier to country_league_label for legend
    legend_order = visible_combos["country_league_label"].tolist()
    legend_domain = visible_combos["country_tier"].tolist()
    legend_range = [color_map[ct] for ct in legend_domain]

    # slider for rating
    slider = alt.binding_range(min=65, max=100, step=1, name='Min Rating: ')
    min_rating_param = alt.param(name='min_rating', value=91, bind=slider)

    main = (
        alt.Chart(df_to_chart)
        .transform_filter(tier_filter)
        .add_params(min_rating_param)
    )


    # strip plot
    points = (
        main
        .mark_circle(
            size=100,
            opacity=0.9
        )
        .encode(
            x=alt.X(
                "Country:N",
                sort=country_order,
                scale=alt.Scale(domain=country_order),
                axis=alt.Axis(titleColor='White', labelColor='White', domain=False),
            ),
            y=alt.Y(
                "Rating:Q",
                scale=alt.Scale(domain=[y_min, y_max], nice=False),
                axis=alt.Axis(
                    domain=False,
                    titleColor='White',
                    labelColor='White',
                    gridOpacity=.5,
                    gridColor='lightgray',
                    gridDash=[2,2],
                ),
            ),
            xOffset="jitter:Q",
            color=alt.Color(
                "country_league_label:N",
                scale=alt.Scale(
                    domain=legend_order,
                    range=legend_range,
                ),
                legend=alt.Legend(
                    title="Country - League",
                    titleColor='White',
                    labelColor='White',
                    orient='right',
                    labelLimit=300,
                ),
            ),
            opacity=alt.condition(
                alt.datum.Rating >= min_rating_param,
                alt.value(0.9),
                alt.value(0.2)
            ),
            tooltip=[
                alt.Tooltip('Team:N', title='Club'),
                alt.Tooltip('League:N', title='League'),
                alt.Tooltip('Country:N', title='Country'),
                alt.Tooltip('Rating:Q', title='Rating')
            ]
        )
        .transform_calculate(
            jitter="clamp(0.02 * sqrt(-2*log(random()))*cos(2*PI*random()), -0.3, 0.3)"
        )
    )

    # create agg data for median
    tiers_to_display_median = df_to_chart[df_to_chart["League Tier"].isin([t for t in ["Tier 1", "Tier 2", "Tier 3"] if t not in hidden_tiers])]
    median_data = (
        tiers_to_display_median.groupby(["Country","country_tier","country_league_label"], as_index=False)["League Median Rating"].mean()
    )

    # median reference lines
    median_lines = (
        alt.Chart(median_data)
        .mark_tick(
            size=75,
            thickness=3,
            opacity=median_line_opacity
        )
        .encode(
            x=alt.X(
                "Country:N",
                sort=country_order,
                scale=alt.Scale(domain=country_order),
            ),
            x2=alt.X2("Country:N"),
            y="League Median Rating:Q",
            color=alt.Color(
                "country_league_label:N",
                scale=alt.Scale(
                    domain=legend_order,
                    range=legend_range,
                ),
                legend=None,
            ),
        )
    )

    # combine strip plot
    strip_plot = (
        (points + median_lines)
        .properties(
            width=600,
            height=400,
            title='Club Ratings by Country'
        )
    )

    # bar chart showing count of visible clubs per league
    bar_chart = (
        main
        .transform_filter(f"datum.Rating >= min_rating")
        .transform_aggregate(
            count='count()',
            groupby=['country_league_label', 'country_tier']
        )
        .mark_bar()
        .encode(
            x=alt.X(
                'count:Q',
                title=f'Number of Clubs',
                axis=alt.Axis(domain=False, titleColor='White', labelColor='White', gridColor='lightgray', gridOpacity=0.5, gridDash=[2, 2])
            ),
            y=alt.Y(
                'country_league_label:N',
                sort='-x',
                title='League',
                axis=alt.Axis(titleColor='White', labelColor='White', labelLimit=300)
            ),
            color=alt.Color(
                "country_league_label:N",
                scale=alt.Scale(
                    domain=legend_order,
                    range=legend_range,
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(
                    'country_league_label:N',
                    title='League'
                ),
                alt.Tooltip(
                    'count:Q',
                    title='Number of Clubs'
                )
            ]
        )
        .properties(
            width=300,
            height=400,
            title=alt.TitleParams(
                text={"expr": "'Clubs per League Rated ' + min_rating + '+'"}
            )
        )
    )

    # combine charts horizontally (bar chart on left, strip plot on right)
    dashboard = (
        alt.hconcat(bar_chart, strip_plot)
        .configure(background='#000000')
        .configure_view(stroke=None)
        .configure_title(color='White')
        .resolve_scale(color='shared')
    )

    return dashboard
