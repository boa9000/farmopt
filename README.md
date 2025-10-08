A tool to find the best allocation of wind turbines in an area on the map. The map is interactive, so a user can input the specified area and the constraints through a map.
## Running in Jupyter Notebook

This tool is designed to be used in a Jupyter notebook environment. For the quickest setup, you can use [Google Colab](https://colab.research.google.com/drive/1AyqrGDcX1nDkmdrQUctnzBWUt25utav9?usp=sharing), which requires no local installation.

### Steps to Run Locally

1. **Install Dependencies**  
    Make sure you have all required Python packages installed. You can use pip:
    ```bash
    pip install -r requirements.txt
    ```

2. **Start Jupyter Notebook**  
    Launch Jupyter Notebook in your project directory:
    ```bash
    jupyter notebook
    ```

2.5. **(optional) Adjust config.yml**
    You can adjust the config.yml file to suit your need if you want to change the economic variables etc.

3. **Import the Interface**  
    In a notebook cell, import the main interface:
    ```python
    from map_interface import MapInterface
    ```

4. **Create the Map Interface**  
    Initialize the map interface and interact with it:
    ```python
    map_ui = MapInterface()
    ```

5. **Configure Area and Constraints**  
    Use the interactive map to specify your area and constraints for wind turbine allocation.
    

### Alternative: Google Colab

If you prefer not to install anything locally, simply open the [Colab link](https://colab.research.google.com/drive/1AyqrGDcX1nDkmdrQUctnzBWUt25utav9?usp=sharing) and follow the instructions in the notebook.
