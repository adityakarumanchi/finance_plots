import pandas as pd
from loguru import logger


def cleanup_df(df: pd.DataFrame, file_path=None):
    df.rename(columns={"Post Date": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month_name()
    logger.info(
        "The `Post Date` column has been renamed to `Date`"
        " and converted to a pandas datetime object"
    )
    # Debits in Chase statements are negative
    if "Chase" in file_path:
        df["Amount"] = -df["Amount"]
    if "Debit" in df.columns:
        df.rename(columns={"Debit": "Amount"}, inplace=True)
    df = df[~(df["Amount"] < 0)]
    df = df.drop(
        columns=df.columns.difference(
            ["Date", "Month", "Amount", "Description", "Category"]
        ),
    )
    df.dropna(inplace=True)
    return df


def load_csv_to_dataframe(file_path):
    """
    Load a CSV file into a pandas DataFrame.

    :param file_path: str, path to the CSV file
    :return: pandas DataFrame
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"CSV file at {file_path} successfully loaded into a DataFrame.")
        df = cleanup_df(df, file_path)
        return df
    except FileNotFoundError:
        logger.error(f"Error: The file at {file_path} was not found.")
    except pd.errors.EmptyDataError:
        logger.error("Error: No data found in the file.")
    except pd.errors.ParserError:
        logger.error("Error: Error parsing the data.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
