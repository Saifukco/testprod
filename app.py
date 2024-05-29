import streamlit as st
import os
import streamlit_authenticator as stauth
from pathlib import Path
import time
from math import radians, cos, sin, asin, sqrt
from streamlit_dynamic_filters import DynamicFilters
import pandas as pd
import pyodbc
# import pypyodbc as odbc
import io
import json
import plotly.express as px
import plotly.graph_objects as go
import base64
import os
import json
import pickle
import uuid
import re
from openai import OpenAI
import datetime
from datetime import datetime, timedelta
import yaml
from yaml.loader import SafeLoader

conn_str="Driver={ODBC Driver 18 for SQL Server};Server=tcp:ukcotestserver.database.windows.net,1433;Database=ukcotestdb;Uid=Saif;Pwd=Ukcotest@;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
conn = odbc.connect(conn_str)
cursor = conn.cursor()

openai_secret_key = os.getenv('openaikey')
client = OpenAI(api_key=openai_secret_key)
col1,=st.columns(1)
with col1:
    st.image('uk_co_logo.jpg',width=150)


def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            #object_to_download = object_to_download.to_csv(index=False)
            towrite = io.BytesIO()
            object_to_download = object_to_download.to_excel(towrite, index=False, header=True)
            towrite.seek(0)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(towrite.read()).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}">{button_text}</a><br></br>'

    return dl_link

# --- USER AUTHENTICATION ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)
names = ["Saif Ali Khan", "Sid Pai"]
usernames = ["saifkhan@ukco.in", "sid@ukco.in"]

name, authentication_status, username = authenticator.login()

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")


if authentication_status:
    st.title(' :robot_face: Gyani')
    filename = 'Output.xlsx'
    with col1:
        st.header(f"Welcome {name}")
    authenticator.logout()
    def main():
        with pyodbc.connect(conn_str) as min_date_conn:
            query = '''
                SELECT MIN(time) as min_date from Naturo.sales_mvisit;
            '''
        min_date = pd.read_sql(sql=query, con=min_date_conn)
        

        with pyodbc.connect(conn_str) as max_date_conn:
            query = '''
                SELECT MAX(time) as max_date from Naturo.sales_mvisit;
            '''
        max_date = pd.read_sql(sql=query, con=max_date_conn)

        with st.sidebar:
            start_date=st.date_input("Start Date",min_date['min_date'][0])
            end_date=st.date_input("End Date",max_date['max_date'][0])

        start_date=start_date.strftime('%Y%m%d')
        end_date=end_date.strftime('%Y%m%d')

        def pie_chart_states(states=None,fy=None):
            with pyodbc.connect(conn_str) as conn:
                query = '''
                    SELECT region, SUM(net_value) as sales FROM
                    (SELECT Naturo.sales_mvisit.time, Naturo.sales_mvisit.outlet_guid, Naturo.sales_mvisit.net_value, Naturo.moutlet4.region FROM Naturo.sales_mvisit
                    INNER JOIN  Naturo.moutlet4 ON Naturo.sales_mvisit.outlet_guid=Naturo.moutlet4.outlet_guid
                    WHERE Naturo.sales_mvisit.net_value>0 AND Naturo.sales_mvisit.time BETWEEN '{}' and '{}') AS tb
                    GROUP BY region;
                '''.format(start_date,end_date)

            df = pd.read_sql(sql=query, con=conn)
            fig_pie = px.pie(df, values='sales', names='region',
                    title='Sales Distribution')
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            download_button_str=download_button(df, filename, f'Click here to download {filename}', pickle_it=False)
            st.markdown(download_button_str, unsafe_allow_html=True)
            return st.plotly_chart(fig_pie)
        
        # Function to create trend chart
        def trend_chart(states=None,fy=None):
            with pyodbc.connect(conn_str) as conn:
                    query = '''
                            SELECT time, region, SUM(net_value) as Sales FROM
                            (SELECT Naturo.sales_mvisit.time, Naturo.sales_mvisit.outlet_guid, Naturo.sales_mvisit.net_value, Naturo.moutlet4.region FROM Naturo.sales_mvisit
                            INNER JOIN  Naturo.moutlet4 ON Naturo.sales_mvisit.outlet_guid=Naturo.moutlet4.outlet_guid
                            WHERE Naturo.sales_mvisit.net_value>0 AND Naturo.sales_mvisit.time BETWEEN '{}' and '{}') AS tb
                            GROUP BY time, region;
                    '''.format(start_date,end_date)
            df = pd.read_sql(sql=query, con=conn)
            if states is None:
                fig_trend = px.line(df.groupby('time').aggregate({'Sales':'sum'}).reset_index(), x='time', y="Sales")
                fig_trend.update_traces(mode = 'lines',line_color='blue')
                download_button_str=download_button(df.groupby('time').aggregate({'Sales':'sum'}).reset_index(), filename, f'Click here to download {filename}', pickle_it=False)
                st.markdown(download_button_str, unsafe_allow_html=True)
            else:
                l_states=states.split(',')
                l_states=[i.strip() for i in l_states]
                fil_df=df.loc[df['region'].isin(l_states)]
                fig_trend = px.line(fil_df.groupby('time').aggregate({'Sales':'sum'}).reset_index(), x='time', y="Sales")
                fig_trend.update_traces(mode = 'lines',line_color='blue')
                download_button_str=download_button(fil_df.groupby('time').aggregate({'Sales':'sum'}).reset_index(), filename, f'Click here to download {filename}', pickle_it=False)
                st.markdown(download_button_str, unsafe_allow_html=True)
            return st.plotly_chart(fig_trend)
        input_text=st.text_input(label="Ask your question...")
        if input_text:
            messages = [{"role": "user", "content": "Yor are acting as a search engine of sales data base. And the sale is in Indian Rupees"}]
            messages.append({"role": "user", "content": input_text})
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "pie_chart_states",
                        "description": "This function shows the distribution of sales in differetnt Indian states. The states are Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry. This returns a plotly pie chart. And also gives the overall summary using the dictionary given",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                    },
                },
                },
                {
                "type": "function",
                    "function": {
                        "name": "trend_chart",
                        "description": "This function shows the trend chart using plotly line chart for the given states it can be multiple states or a single state and also explains the over analysis and the sale growth or degrowth overtime, And also gives the overall summary using the dictionary give",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                        }, 
                    },  
                },
                {
                "type": "function",
                    "function": {
                        "name": "outlets_metrics",
                        "description": "This function shows the metrices of the outlets",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names. And also gives the overall summary using the dictionary give",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                    },
                    },   
                },
                {
                "type": "function",
                "function": {
                    "name": "map_chart",
                    "description": "This function displays the outlets or the retailor shop locations on the map using plotly scatter_mapbox and also the table which sale by state and outlet. And also gives the overall summary using the dictionary given based on top performing oultes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "states": {
                                "type": "string",
                                "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                            },
                            "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                        },
                        "required": ["states"],
                    },
                },
                },
                {
                "type": "function",
                    "function": {
                        "name": "top_sel_sku",
                        "description": "This function gives the top selling SKU's that is Stock Keeping Units. If the states are mentioned it considers the states as well. SKU's and Stock Keeping Units are same",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                        }, 
                    },  
                },
                {
                "type": "function",
                    "function": {
                        "name": "top_salesmen",
                        "description": "This function gives the top salesmen by their average sales in respective sates, and ASM that is Area Sales manager",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                        }, 
                    },   
                },
                {
                "type": "function",
                    "function": {
                        "name": "top_beats",
                        "description": "This function gives the top beats by their average sales in respective sates",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                        }, 
                    },  
                },
                {
                 "type": "function",
                    "function": {
                        "name": "new_outlets",
                        "description": "This function gives the details of new oultes or shops by sates and and also the number of new outlets",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "states": {
                                    "type": "string",
                                    "description": "The Indian state, e.g. Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka,Puducherry, Pondicherry it can be multiple states or a single state, use the full names",
                                },
                                "fy": {"type": "string", "description":"This the Indian Financial years like FY 21 ,FY 22 ,FY 23 ,FY 24 and so on. if it is FY 21 it means Financial year 2021. these are the values in data FY 21 ,FY 22 ,FY 23 ,FY 24"},
                            },
                        }, 
                    },   
                }
            ]
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                tools=tools,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            # Step 2: check if the model wanted to call a function
            if tool_calls:
                # Step 3: call the function
                # Note: the JSON response may not always be valid; be sure to handle errors
                available_functions = {
                    "pie_chart_states": pie_chart_states,
                    "trend_chart": trend_chart,
                }  # only one function in this example, but you can have multiple
                messages.append(response_message)  # extend conversation with assistant's reply
                # Step 4: send the info for each function call and function response to the model
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(
                        states=function_args.get("states"),
                        fy=function_args.get("fy")
                    )
                    messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response
                }
            )  # extend conversation with function response
                print(messages)
                try:
                    second_response = client.chat.completions.create(
                        model="gpt-3.5-turbo-1106",
                        messages=messages,
                    )
                    return st.write(second_response.choices[0].message.content)
                except:
                    pass
                    
        else:
            return None
        
        
    





    # Run the main function
    if __name__ == '__main__':
        main()
