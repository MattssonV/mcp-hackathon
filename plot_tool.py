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
    csv_data: str, plot_type: str, x_col: str, y_col: str, file_path: str = None
) -> Image:
    """
    Generates a plot (line or bar) from CSV data and returns a PNG image.

    :param csv_data: CSV data as a string.
    :param plot_type: The type of plot to create ('line' or 'bar').
    :param x_col: The column name for the X-axis.
    :param y_col: The column name for the Y-axis.
    :param file_path: Optional path to save the image file.
    :return: An Image object containing the generated PNG plot.
    """
    try:
        # Read the CSV data from the string
        data = pd.read_csv(io.StringIO(csv_data))

        # Attempt to parse columns with stringified lists/dicts
        for col in data.columns:
            if data[col].dtype == object:
                try:
                    # Try parsing the first non-null value
                    sample = data[col].dropna().iloc[0]
                    if isinstance(sample, str) and (
                        sample.startswith("[") or sample.startswith("{")
                    ):
                        data[col] = data[col].apply(
                            lambda x: ast.literal_eval(x) if pd.notnull(x) else x
                        )
                except Exception:
                    pass  # If parsing fails, leave as is

        # If the x_col or y_col is a list of dicts, flatten it
        if data[x_col].apply(lambda x: isinstance(x, list)).any():
            # Explode the list and normalize
            data = data.explode(x_col)
            data = data.reset_index(drop=True)
            data[x_col] = data[x_col].apply(lambda x: x if isinstance(x, dict) else {})
            # If y_col is inside the dict, extract it
            if all(isinstance(x, dict) and y_col in x for x in data[x_col]):
                data[y_col] = data[x_col].apply(lambda x: x[y_col])
                data[x_col] = data[x_col].apply(lambda x: x.get("Name", str(x)))

        # Create the plot
        plt.figure(figsize=(10, 6))

        if plot_type.lower() == "line":
            plt.plot(data[x_col], data[y_col])
            plt.title("Line Chart")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        elif plot_type.lower() == "bar":
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
