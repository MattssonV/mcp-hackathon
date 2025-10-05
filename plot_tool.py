import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
from fastmcp import FastMCP
from fastmcp.utilities.types import Image  # Use this helper class for image returns
import tempfile
import json
import ast

# 1. Initialize the FastMCP server
mcp = FastMCP("PlottingServer 📊")


@mcp.tool
def get_json_data(filepath: str) -> str:
    """
    Reads a JSON file and returns its content as a CSV string.
    :param filepath: Path to the JSON file.
    :return: CSV string with JSON content.
    """
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return ""
    except PermissionError:
        print(f"Permission denied: {filepath}")
        return ""
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""
    df = pd.json_normalize(data)
    csv_data = df.to_csv(index=False)
    return csv_data


# 2. Define the tool with parameters
@mcp.tool
def generate_plot(
    csv_data: str,
    plot_type: str,
    x_col: str,
    y_col: str,
    group_col: str = None,
    file_path: str = None,
) -> Image:
    """
    Generates a plot (line or bar) from CSV data and returns a PNG image.
    Supports multiple lines if a group_col is provided.
    Also flattens columns containing stringified lists of dicts (e.g., Skaters column).

    :param csv_data: CSV data as a string.
    :param plot_type: The type of plot to create ('line' or 'bar').
    :param x_col: The column name for the X-axis.
    :param y_col: The column name for the Y-axis.
    :param group_col: Optional column name to group by for multiple lines.
    :param file_path: Optional path to save the image file.
    :return: An Image object containing the generated PNG plot.
    """
    try:
        # Read the CSV data from the string
        data = pd.read_csv(io.StringIO(csv_data))

        # Flatten columns with stringified lists of dicts (e.g., Skaters)
        for col in data.columns:
            if data[col].dtype == object:
                try:
                    sample = data[col].dropna().iloc[0]
                    if (
                        isinstance(sample, str)
                        and sample.startswith("[")
                        and "{" in sample
                    ):
                        # Assume this is a stringified list of dicts
                        # Explode the column so each dict becomes a row
                        expanded_rows = []
                        for idx, row in data.iterrows():
                            try:
                                items = ast.literal_eval(row[col])
                                if isinstance(items, list):
                                    for item in items:
                                        new_row = row.to_dict()
                                        if isinstance(item, dict):
                                            for k, v in item.items():
                                                new_row[k] = v
                                        expanded_rows.append(new_row)
                                else:
                                    expanded_rows.append(row.to_dict())
                            except Exception:
                                expanded_rows.append(row.to_dict())
                        data = pd.DataFrame(expanded_rows)
                except Exception:
                    pass  # If parsing fails, leave as is

        # Attempt to parse columns with stringified dicts
        for col in data.columns:
            if data[col].dtype == object:
                try:
                    sample = data[col].dropna().iloc[0]
                    if isinstance(sample, str) and (sample.startswith("{")):
                        data[col] = data[col].apply(
                            lambda x: ast.literal_eval(x) if pd.notnull(x) else x
                        )
                except Exception:
                    pass

        # Ensure y_col is numeric and drop invalid rows
        if y_col in data.columns:
            data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
            data = data.dropna(subset=[y_col])

        # If after cleaning, no data remains, return an empty image
        if data.empty:
            print("No valid data to plot after cleaning.")
            return Image(b"", format="png")

        plt.figure(figsize=(10, 6))

        if plot_type.lower() == "line":
            if group_col and group_col in data.columns:
                for key, grp in data.groupby(group_col):
                    plt.plot(grp[x_col], grp[y_col], label=str(key))
                plt.legend(title=group_col)
            else:
                plt.plot(data[x_col], data[y_col])
            plt.title("Line Chart")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        elif plot_type.lower() == "bar":
            if group_col and group_col in data.columns:
                for key, grp in data.groupby(group_col):
                    plt.bar(grp[x_col], grp[y_col], label=str(key))
                plt.legend(title=group_col)
            else:
                plt.bar(data[x_col], data[y_col])
            plt.title("Bar Chart")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        else:
            raise ValueError(f"Unsupported plot type: {plot_type}")

        if file_path:
            plt.savefig(file_path, format="png")
            img_path = file_path
        else:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                plt.savefig(tmp, format="png")
                img_path = tmp.name
        plt.close()
        with open(img_path, "rb") as img_file:
            img_bytes = img_file.read()

        return Image(data=img_bytes, format="png")

    except Exception as e:
        print(f"An error occurred during plotting: {e}")
        return Image(b"", format="png")


# 5. Run the server
if __name__ == "__main__":
    mcp.run()
