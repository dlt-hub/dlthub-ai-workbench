import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md("# Rick and Morty Data Explorer")
    return (mo,)


@app.cell
def _():
    import dlt
    import ibis

    pipeline = dlt.attach("rick_and_morty")
    dataset = pipeline.dataset()
    return dataset, ibis, pipeline


@app.cell
def _(dataset, mo):
    mo.md("## Overview")
    return


@app.cell
def _(dataset):
    row_counts = dataset.row_counts().to_ibis()
    row_counts
    return


@app.cell
def _(dataset):
    character = dataset["character"].to_ibis()
    location = dataset["location"].to_ibis()
    episode = dataset["episode"].to_ibis()
    char_episode = dataset["character__episode"].to_ibis()
    ep_characters = dataset["episode__characters"].to_ibis()
    loc_residents = dataset["location__residents"].to_ibis()
    return char_episode, character, ep_characters, episode, loc_residents, location


@app.cell
def _(mo):
    mo.md("## Character Demographics")
    return


@app.cell
def _(alt, character, mo):
    _status = character.group_by("status").aggregate(count=character.id.count())
    chart_status = mo.ui.altair_chart(
        alt.Chart(_status.to_pandas())
        .mark_arc(innerRadius=50)
        .encode(
            theta="count:Q",
            color=alt.Color("status:N", scale=alt.Scale(domain=["Alive", "Dead", "unknown"], range=["#2ecc71", "#e74c3c", "#95a5a6"])),
            tooltip=["status", "count"],
        )
        .properties(title="Status", width=250, height=250)
    )
    chart_status
    return


@app.cell
def _(alt, character, ibis, mo):
    _species = (
        character.group_by("species")
        .aggregate(count=character.id.count())
        .order_by(ibis.desc("count"))
        .limit(10)
    )
    chart_species = mo.ui.altair_chart(
        alt.Chart(_species.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Characters"),
            y=alt.Y("species:N", sort="-x", title="Species"),
            color=alt.value("#3498db"),
            tooltip=["species", "count"],
        )
        .properties(title="Top 10 Species", width=400, height=300)
    )
    chart_species
    return


@app.cell
def _(alt, character, mo):
    _gender = character.group_by("gender").aggregate(count=character.id.count())
    chart_gender = mo.ui.altair_chart(
        alt.Chart(_gender.to_pandas())
        .mark_arc(innerRadius=50)
        .encode(
            theta="count:Q",
            color="gender:N",
            tooltip=["gender", "count"],
        )
        .properties(title="Gender Distribution", width=250, height=250)
    )
    chart_gender
    return


@app.cell
def _(mo):
    mo.md("## Character Appearances")
    return


@app.cell
def _(char_episode, character, ibis):
    appearances = (
        character.join(char_episode, character._dlt_id == char_episode._dlt_parent_id)
        .group_by("name", "status", "species")
        .aggregate(episode_count=char_episode._dlt_list_idx.count())
        .order_by(ibis.desc("episode_count"))
    )
    appearances
    return (appearances,)


@app.cell
def _(alt, appearances, mo):
    _top20 = appearances.limit(20)
    chart_appearances = mo.ui.altair_chart(
        alt.Chart(_top20.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("episode_count:Q", title="Episodes"),
            y=alt.Y("name:N", sort="-x", title="Character"),
            color="status:N",
            tooltip=["name", "species", "status", "episode_count"],
        )
        .properties(title="Top 20 Characters by Episode Count", width=500, height=400)
    )
    chart_appearances
    return


@app.cell
def _(mo):
    mo.md("## Episodes by Season")
    return


@app.cell
def _(episode, ibis):
    episodes_by_season = (
        episode.mutate(season=episode.episode.left(3))
        .group_by("season")
        .aggregate(
            episodes=episode.id.count(),
        )
        .order_by("season")
    )
    episodes_by_season
    return


@app.cell
def _(ep_characters, episode, ibis):
    cast_size = (
        episode.join(ep_characters, episode._dlt_id == ep_characters._dlt_parent_id)
        .group_by("name", "episode", "air_date")
        .aggregate(cast_size=ep_characters._dlt_list_idx.count())
        .mutate(season=ibis._.episode.left(3))
        .order_by(ibis.desc("cast_size"))
    )
    cast_size
    return


@app.cell
def _(alt, cast_size, mo):
    chart_cast = mo.ui.altair_chart(
        alt.Chart(cast_size.to_pandas())
        .mark_point(filled=True, size=60)
        .encode(
            x=alt.X("episode:N", title="Episode", sort=None),
            y=alt.Y("cast_size:Q", title="Characters in Episode"),
            color="season:N",
            tooltip=["name", "episode", "air_date", "cast_size"],
        )
        .properties(title="Cast Size per Episode", width=600, height=300)
    )
    chart_cast
    return


@app.cell
def _(mo):
    mo.md("## Location Analysis")
    return


@app.cell
def _(ibis, loc_residents, location):
    location_stats = (
        location.join(loc_residents, location._dlt_id == loc_residents._dlt_parent_id, how="left")
        .group_by("name", "type", "dimension")
        .aggregate(residents=loc_residents._dlt_list_idx.count())
        .order_by(ibis.desc("residents"))
    )
    location_stats
    return (location_stats,)


@app.cell
def _(alt, ibis, location, mo):
    _loc_types = (
        location.filter(location.type != "")
        .group_by("type")
        .aggregate(count=location.id.count())
        .order_by(ibis.desc("count"))
        .limit(10)
    )
    chart_loc_types = mo.ui.altair_chart(
        alt.Chart(_loc_types.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Locations"),
            y=alt.Y("type:N", sort="-x", title="Type"),
            color=alt.value("#9b59b6"),
            tooltip=["type", "count"],
        )
        .properties(title="Location Types", width=400, height=300)
    )
    chart_loc_types
    return


@app.cell
def _(alt, ibis, location, mo):
    _dims = (
        location.filter((location.dimension != "") & (location.dimension != "unknown"))
        .group_by("dimension")
        .aggregate(count=location.id.count())
        .order_by(ibis.desc("count"))
        .limit(10)
    )
    chart_dims = mo.ui.altair_chart(
        alt.Chart(_dims.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Locations"),
            y=alt.Y("dimension:N", sort="-x", title="Dimension"),
            color=alt.value("#e67e22"),
            tooltip=["dimension", "count"],
        )
        .properties(title="Top Dimensions", width=400, height=300)
    )
    chart_dims
    return


@app.cell
def _():
    import altair as alt

    return (alt,)


if __name__ == "__main__":
    app.run()
