from import_csvs import load_csv_to_dataframe
from os.path import join, expanduser
from os import listdir, getcwd
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

target_dir = join(expanduser("~"), "Documents/Statements/")
statement_dfs = []


# Only for the Citi statement, coz no category in it
def set_category(df_in: pd.DataFrame):
    # Assumption: Q2 2024 spending was on Groceries, Q3 on Restaurants
    df_in["Category"] = ["Groceries"] * df_in["Date"].size
    df_in.loc[
        (df_in["Date"] > pd.to_datetime("2024-06-30"))
        & (df_in["Date"] <= pd.to_datetime("2024-09-30")),
        "Category",
    ] = "Restaurants"


for file in listdir(target_dir):
    if file.lower().endswith(".csv"):
        df = load_csv_to_dataframe(join(target_dir, file))
        if "Category" not in df.columns:
            set_category(df)
        statement_dfs.append(df)

if __name__ == "__main__":
    spending_data = pd.concat(statement_dfs, axis=0, ignore_index=True)
    spending_data["Category"] = pd.Categorical(spending_data["Category"])
    spending_data.sort_values(
        by=["Date"], ascending=True, inplace=True, ignore_index=True
    )

    spending_data["Monthly_cumulative"] = (
        spending_data[["Month", "Amount"]].groupby("Month").cumsum()
    )
    # print(spending_data[["Date", "Monthly_cumulative"]])
    save_to_disk = ""  # "csv"
    if save_to_disk == "feather":
        spending_data.to_feather(join(getcwd(), "combined_and_sorted_data"))
    elif save_to_disk == "csv":
        spending_data.to_csv(join(getcwd(), "combined_and_sorted_data.csv"))

    categorical_totals = (
        spending_data[["Category", "Amount"]].groupby("Category", observed=True).sum()
    )
    monthly_totals = spending_data[["Month", "Amount"]].groupby("Month").sum()

    plotting_on = True
    if plotting_on:
        # fig_totals = make_subplots(rows=2)
        # fig_totals.add_bar(
        #     # go.Bar(categorical_totals, x="Category", y="Amount", color="Category"),
        #     px.bar(categorical_totals, x="Category", y="Amount", color="Category"),
        #     row=1,
        # )
        # fig_totals.add_trace(monthly_totals, x="Month", y="Amount")

        app = dash.Dash(__name__)

        app.layout = html.Div(
            [
                html.H1("Monthly Data Plot"),
                dcc.Dropdown(
                    id="month-dropdown",
                    options=[
                        {"label": month, "value": month}
                        for month in spending_data["Month"].unique()
                    ],
                    value="January",
                ),
                dcc.Dropdown(
                    id="category-dropdown",
                    options=[
                        {"label": category, "value": category}
                        for category in df["Category"].unique()
                    ]
                    + [{"label": "All Categories", "value": "All Categories"}],
                    value="All Categories",
                ),
                dcc.Graph(id="monthly-plot"),
                dcc.Graph(id="category-plot"),
            ]
        )

        plot_col = "Monthly_cumulative"

        @app.callback(
            [Output("monthly-plot", "figure"), Output("category-plot", "figure")],
            [Input("month-dropdown", "value"), Input("category-dropdown", "value")],
        )
        def update_figure(selected_month, selected_category):
            filtered_df = spending_data[spending_data["Month"] == selected_month]

            cumul_fig = px.line(
                filtered_df,
                x="Date",
                y=plot_col,
                title=f"Data for {selected_month} (All Categories)",
            )
            if selected_category == "All Categories":
                category_fig = px.bar(
                    filtered_df,
                    x="Category",
                    y="Amount",
                    title=f"Total Data for {selected_month} (All Categories)",
                    color="Category",
                )
            else:
                filtered_df = filtered_df[filtered_df["Category"] == selected_category]
                category_fig = px.line(
                    filtered_df["Date"],
                    filtered_df["Amount"].cumsum(),
                    title=f"Data for {selected_month} ({selected_category})",
                )

            return cumul_fig, category_fig

        app.run_server(debug=True)
