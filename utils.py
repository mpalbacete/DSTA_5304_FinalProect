import pandas as pd
import colorsys

def get_data(filename):
    df = pd.read_csv(f'{filename}')
    df = df[df['Region'] == 'Europe'] #filter to Europe Only

    #add country|tier Concat
    df['Country|Tier'] = df['Country'].astype(str) + "|" + df['League Tier'].astype(str)

    # get median league rating
    league_median_rating = df.groupby(["League", "Country"])["Rating"].median().to_frame("League Median Rating")

    # get max median rating within each country and rank countries based on the max (ie. if Premier League is median of 85, then england shoud be ranked 1st in country list, even though there are other leagues with lower median ratings)
    max_median_in_country = league_median_rating.groupby("Country")["League Median Rating"].max().to_frame("Max Median Rating in Country")
    max_median_in_country['Country Rank'] = max_median_in_country["Max Median Rating in Country"].rank(ascending=False)

    # merge data back together after getting stats
    df = pd.merge(df, league_median_rating, on="League")
    df = pd.merge(df, max_median_in_country, on="Country")

    # only show a total of 12 countries
    df_to_show = df[df["Country Rank"] <= 12].copy()

    return df_to_show


def adjust_lightness(hex_color, factor):
    # remove hash
    hex_color = hex_color.lstrip("#")

    #convert out of hex to rgb
    r, g, b = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

    # get hls from rgb
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # scale lightness based on factor
    l = max(0, min(1, l * factor))

    # remap back to an rgb value
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)

    # return hex value
    return "#{:02x}{:02x}{:02x}".format(int(r2*255), int(g2*255), int(b2*255))

def add_colors_to_df(df):
    # map color pallet to leagues (leagues in same country should have similar colors for ease of reading)
    color_palette = [
        "#264653",
        "#2A9D8F",
        "#E9C46A",
        "#F4A261",
        "#E76F51",
        "#6D597A",
        "#355070",
        "#B56576",
        "#457B9D",
        "#8AB17D",
        "#BC6C25",
        "#5F0F40",
    ]

    # Tier brightness scaling
    tier_factors = {
        "Tier 1": 1.5,  # lightest
        "Tier 2": 1.0,
        "Tier 3": .5,  # darkest
    }

    #find unique countries and map the base level hex codes to those countries
    unique_countries = sorted(df["Country"].unique())
    country_colors = dict(zip(unique_countries, color_palette))

    # assign adjusted brightness of color based on tier
    color_map = {}
    for country in unique_countries:
        for tier, factor in tier_factors.items():
            color_map[f"{country}|{tier}"] = adjust_lightness(country_colors[country], factor)

    # add assigned hex color back to dataframe
    df['Hex Color'] = df['Country|Tier'].map(color_map)

    return df

def get_country_sort_order(df):
    # find country order (relevant for charting sort order used later
    country_order = (
        df
        .groupby("Country")["Country Rank"]
        .max()
        .sort_values(ascending=True)
        .index
        .tolist()
    )
    return country_order