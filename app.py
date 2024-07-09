import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import streamlit.components.v1 as components
import plotly.express as px
import seaborn as sns
import io
import base64


# Define app1
def app1():
    file_path = "police_killings.csv"
    data = pd.read_csv(file_path, encoding='ISO-8859-1')
    data = data.dropna(subset=['longitude', 'latitude'])
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    data = data.dropna(subset=['longitude', 'latitude'])
    data = data[(data['latitude'] >= -90) & (data['latitude'] <= 90)]
    data = data[(data['longitude'] >= -180) & (data['longitude'] <= 180)]

    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
    heat_data = [[row['latitude'], row['longitude']] for index, row in data.iterrows()]
    HeatMap(heat_data).add_to(m)

    legend_html = '''
         <div style="position: fixed;
         bottom: 50px; left: 50px; width: 150px; height: auto;
         background-color: white; z-index:9999; font-size:14px;
         border:2px solid grey; border-radius:6px; padding: 10px;">
         <b>Heatmap Legend</b><br>
         <i style="background:rgba(0, 0, 255, 1); width:18px; height:18px; display:inline-block; margin-right:5px; border:1px solid black;"></i> Low Intensity<br>
         <i style="background:rgba(0, 255, 0, 1); width:18px; height:18px; display:inline-block; margin-right:5px; border:1px solid black;"></i> Medium Intensity<br>
         <i style="background:rgba(255, 0, 0, 1); width:18px; height:18px; display:inline-block; margin-right:5px; border:1px solid black;"></i> High Intensity
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))
    m.save('police_killings_heatmap.html')

    st.title('Police Killings Heatmap')
    components.html(open('police_killings_heatmap.html', 'r').read(), height=600)


# Define app2
def app2():
    file_path = "police_killings.csv"
    data = pd.read_csv(file_path, encoding='ISO-8859-1')
    data.rename(columns={'raceethnicity': 'race/ethnicity'}, inplace=True)
    data['age'] = pd.to_numeric(data['age'], errors='coerce')
    data.dropna(subset=['age'], inplace=True)
    bins = [0, 18, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ['0-18', '19-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
    data['age_group'] = pd.cut(data['age'], bins=bins, labels=labels, right=False)
    data['age_group'] = data['age_group'].astype('category')
    data['armed_binary'] = data['armed'].apply(lambda x: 'Yes' if x != 'No' and x != 'Unknown' else 'No')
    data = data[data['race/ethnicity'] != 'Unknown']

    column_options = [
        {'label': 'Gender', 'value': 'gender'},
        {'label': 'Race/Ethnicity', 'value': 'race/ethnicity'},
        {'label': 'Month', 'value': 'month'},
        {'label': 'Age Group', 'value': 'age_group'},
        {'label': 'Armed', 'value': 'armed_binary'}
    ]

    st.title('Distribution of Police Killings by Race/Ethnicity and Other Factors')
    selected_column = st.selectbox('Select Column to Represent', options=[col['value'] for col in column_options],
                                   format_func=lambda x: next(
                                       item['label'] for item in column_options if item['value'] == x))

    # Ensure selected column is sorted by count
    if selected_column == 'age_group':
        data[selected_column] = data[selected_column].astype(str)
        category_order = ['0-18', '19-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
    elif selected_column == 'month':
        data[selected_column] = pd.Categorical(data[selected_column], categories=[
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], ordered=True)
        category_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    else:
        category_order = data[selected_column].value_counts().index.tolist()

    # Sort data by race/ethnicity and selected column
    data = data.sort_values(by=['race/ethnicity', selected_column], ascending=[True, True])

    fig = px.histogram(
        data,
        x='race/ethnicity',
        color=selected_column,
        barmode='group',
        category_orders={'race/ethnicity': data['race/ethnicity'].value_counts().index.tolist(),
                         selected_column: category_order},
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig.update_layout(
        title=f'Distribution of Police Killings by Race/Ethnicity and {selected_column.replace("_", " ").capitalize()} in 2015',
        xaxis_title='Race/Ethnicity',
        yaxis_title='Number of Police Killings',
        legend_title=selected_column.replace("_", " ").capitalize()
    )
    st.plotly_chart(fig)


# Define app3
def app3():
    file_path = "police_killings.csv"
    data = pd.read_csv(file_path, encoding='ISO-8859-1')

    socio_economic_columns = {
        'pov': 'Poverty rate',
        'pop': 'Tract population',
        'h_income': 'Tract-level median household income',
        'urate': 'Tract-level unemployment rate',
        'county_income': 'County-level median household income',
        'college': 'College completion rate'
    }

    for col in socio_economic_columns.keys():
        data[col] = pd.to_numeric(data[col], errors='coerce')

    st.title('Socio-Economic Variables Pair Plot')
    selected_columns = st.multiselect(
        'Select Socio-Economic Variables to Plot',
        options=list(socio_economic_columns.keys()),
        default=list(socio_economic_columns.keys())[:3],
        format_func=lambda x: socio_economic_columns[x]
    )

    if len(selected_columns) < 2:
        st.warning('Please select at least two variables.')
        return

    socio_economic_data = data[selected_columns].copy()
    socio_economic_data.columns = [socio_economic_columns[col] for col in selected_columns]

    sns.set(style="ticks")
    pairplot = sns.pairplot(socio_economic_data, diag_kind="kde", height=4, aspect=1)

    for ax in pairplot.axes.flatten():
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

    buf = io.BytesIO()
    pairplot.savefig(buf, format="png", dpi=200)
    buf.seek(0)

    encoded_image = base64.b64encode(buf.read()).decode('utf-8')
    st.image(f'data:image/png;base64,{encoded_image}')


# Main Streamlit app
st.sidebar.title("Navigation")
st.sidebar.markdown("<style>.css-1d391kg {color: red;}</style>", unsafe_allow_html=True)
app_selection = st.sidebar.radio("Go to", ["Heatmap", "Bar Chart", "Pair Plot"])

if app_selection == "Heatmap":
    app1()
elif app_selection == "Bar Chart":
    app2()
elif app_selection == "Pair Plot":
    app3()
