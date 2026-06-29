

# To run the web app :
- In pycharm terminal, run the command "streamlit run web_app.py" in the project folder.
- open a web page with url "http://localhost:8501/"
- to close/stop the app do ctrl+c in the terminal

OR you can also create a new pycharm run configuration to run it using :
- a (new) python run configuration
- with your python interpreter
- with, instead of 'script' by default, 'module' with the value 'streamlit'
- and with parameters 'run web_app.py'


# Prerequisites :
pip install "rembg[gpu]" (for Nvidia) or pip install "rembg[cpu]" or ... cf here https://github.com/danielgatis/rembg#installation
