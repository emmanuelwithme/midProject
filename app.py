import flask
import pandas
import numpy
import plotly
import json
import plotly.express as px

app1 = flask.Flask("__name__")

data_url = "https://sip.einvoice.nat.gov.tw/ods-main/ODS308E/download/3886F055-EB77-4DF9-98E2-F3F49A7D3434/1/E265F67E-6CDA-4FB2-B4E9-ACF40ECA3476/0/?fileType=csv"
data = pandas.read_csv(data_url, encoding='utf8', usecols=["發票年月","縣市代碼","縣市名稱","鄉鎮市區代碼","鄉鎮市區名稱","行業名稱","平均開立張數","平均開立金額","平均客單價"])

@app1.route("/")
def hello():
    return flask.render_template("home.html")

@app1.route("/selectDistrict")
def selectDistrict():
    return flask.render_template("selectDistrict.html")

@app1.route("/selectDistrictVS")
def selectDistrictVS():
    return flask.render_template("selectDistrictVS.html")

# selectDistrict.html 中的city下拉式選單顯示出來
@app1.route("/getCity", methods=["GET"])
def getCity():
    dataCity = data["縣市名稱"].drop_duplicates()
    result = dataCity.to_json(orient="values")
    parsed = json.loads(result)
    json_string = json.dumps(parsed, ensure_ascii=False).encode('utf8')
    print("json_string.decode(): ", json_string.decode(), "type: ",
            type(json_string.decode())) #json_string.decode() is a str

    #convert string to  object
    json_object = json.loads(json_string.decode())
    #check new data type
    print("json_object: ",json_object,"type: ",type(json_object)) # json_object is a list
    return json_object

# selectDistrict.html 中選擇 縣市名稱 後，鄉鎮市區名稱 下拉式選單顯示出來
@app1.route("/getDistrict", methods=["POST"])
def getDistrict():
    city = flask.request.form.get('city')
    print(city, type(city))

    filter_City = (data["縣市名稱"] == city)
    # 去除該縣市中，重複的區
    dataDistricts = data[filter_City]["鄉鎮市區名稱"].drop_duplicates()
    # dataframe to json
    result = dataDistricts.to_json(orient="values")
    parsed = json.loads(result)
    json_string = json.dumps(parsed, ensure_ascii=False).encode('utf8')
    print("json_string.decode(): ", json_string.decode(), "type: ",
          type(json_string.decode()))  # json_string.decode() is a str

    # convert string to  object
    json_object = json.loads(json_string.decode())
    # check new data type
    print("json_object: ", json_object, "type: ",
          type(json_object))  # json_object is a list
    return json_object

@app1.route("/getIndustry",methods=["POST"])
def getIndustry():
    city = flask.request.form.get('city')
    district = flask.request.form.get('district')
    print(city, type(city))
    print(district, type(district))

    filter_City = (data["縣市名稱"] == city)
    filter_District = (data["鄉鎮市區名稱"] == district)
    # 去除該縣市中，重複的區
    dataIndustry = data[filter_City&filter_District]["行業名稱"].drop_duplicates()
    result = dataIndustry.to_json(orient="values")
    parsed = json.loads(result)
    json_string = json.dumps(parsed, ensure_ascii=False).encode('utf8')
    print("json_string.decode(): ", json_string.decode(), "type: ",
            type(json_string.decode())) #json_string.decode() is a str

    #convert string to  object
    json_object = json.loads(json_string.decode())
    #check new data type
    print("json_object: ",json_object,"type: ",type(json_object)) # json_object is a list
    return json_object

@app1.route("/monthlyGrowthRate")
def monthlyGrowthRate():
    city = flask.request.args.get("city")
    district = flask.request.args.get("district")
    industry = flask.request.args.get("industry")

    filter_City = (data['縣市名稱'] == city)
    filter_District = (data['鄉鎮市區名稱'] == district)
    filter_Industry = (data['行業名稱'] == industry)

    # data_new篩選出來特定地區特定產業
    data_new=data[filter_City&filter_District&filter_Industry].sort_values(by=['發票年月'],ascending=False)
    data_new['平均開立張數月成長率'] = numpy.NaN
    data_new['平均開立金額月成長率'] = numpy.NaN
    data_new['平均客單價月成長率'] = numpy.NaN
    data_new.reset_index(inplace = True,drop = True) #把原本的index_col drop

    for index in range(len(data_new.index)-1):
        # at[資料索引值,欄位名稱]：利用資料索引值及欄位名稱來取得「單一值」
        data_new.at[index,'平均開立張數月成長率'] = (data_new.at[index,'平均開立張數'] - data_new.at[index+1,'平均開立張數'])/data_new.at[index+1,'平均開立張數']
        data_new.at[index,'平均開立金額月成長率'] = (data_new.at[index,'平均開立金額'] - data_new.at[index+1,'平均開立金額'])/data_new.at[index+1,'平均開立金額']
        data_new.at[index,'平均客單價月成長率'] = (data_new.at[index,'平均客單價'] - data_new.at[index+1,'平均客單價'])/data_new.at[index+1,'平均客單價']

    # 發票年月 轉成 yyyy-MM 型態字串 方便 plotly繪圖辨識時間
    data_new['發票年月'] = (data_new['發票年月']/100).astype('int').astype('str')+'-'+(data_new['發票年月']%100).astype('int').astype('str')
    print(data_new)

    # here I'm adding a column "Num_Color" with colors
    # "平均開立張數月成長率"正為紅色，負為綠色
    data_new["Num_Color"] = numpy.where(data_new["平均開立張數月成長率"]<0, 'green', 'red')
    fig1 = px.bar(data_new, x='發票年月', y='平均開立張數月成長率')
    fig1.update_traces(marker_color=data_new["Num_Color"])
    # fig1.show(renderer='colab')
    graphJSON1 = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

    # here I'm adding a column "Sum_Color" with colors
    # "平均開立金額月成長率"正為紅色，負為綠色
    data_new["Sum_Color"] = numpy.where(data_new["平均開立金額月成長率"]<0, 'green', 'red')
    fig2 = px.bar(data_new, x='發票年月', y='平均開立金額月成長率')
    fig2.update_traces(marker_color=data_new["Sum_Color"])
    # fig2.show(renderer='colab')
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # here I'm adding a column "Per_Price_Color" with colors
    # "平均客單價月成長率"正為紅色，負為綠色
    data_new["Per_Price_Color"] = numpy.where(data_new["平均客單價月成長率"]<0, 'green', 'red')
    fig3 = px.bar(data_new, x='發票年月', y='平均客單價月成長率')
    fig3.update_traces(marker_color=data_new["Per_Price_Color"])
    # fig3.show(renderer='colab')
    graphJSON3 = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)

    return flask.render_template("monthlyGrowthRate.html",graphJSON1=graphJSON1,graphJSON2=graphJSON2,graphJSON3=graphJSON3,city=city,district=district,industry=industry)

# 比較兩個地區同產業 的 平均開立張數月成長率、平均開立金額月成長率、平均客單價月成長率
@app1.route("/monthlyGrowthRateVS",methods=["GET"])
def monthlyGrowthRateVS():
    city1 = flask.request.args.get("city1")
    district1 = flask.request.args.get("district1")
    industry1 = flask.request.args.get("industry1")

    city2 = flask.request.args.get("city2")
    district2 = flask.request.args.get("district2")
    industry2 = flask.request.args.get("industry2")

    filter_City = (data['縣市名稱'] == city1)
    filter_District = (data['鄉鎮市區名稱'] == district1)
    filter_Industry = (data['行業名稱'] == industry1)

    filter_City2 = (data['縣市名稱'] == city2)
    filter_District2 = (data['鄉鎮市區名稱'] == district2)
    filter_Industry2 = (data['行業名稱'] == industry2)

    data_new=data[filter_City&filter_District&filter_Industry].sort_values(by=['發票年月'],ascending=False)
    data_new['平均開立張數月成長率'] = numpy.NaN
    data_new['平均開立金額月成長率'] = numpy.NaN
    data_new['平均客單價月成長率'] = numpy.NaN
    data_new.reset_index(inplace = True,drop = True) #把原本的index_col drop

    data_new2=data[filter_City2&filter_District2&filter_Industry2].sort_values(by=['發票年月'],ascending=False)
    data_new2['平均開立張數月成長率'] = numpy.NaN
    data_new2['平均開立金額月成長率'] = numpy.NaN
    data_new2['平均客單價月成長率'] = numpy.NaN
    data_new2.reset_index(inplace = True,drop = True) #把原本的index_col drop

    for index in range(len(data_new.index)-1):
        # at[資料索引值,欄位名稱]：利用資料索引值及欄位名稱來取得「單一值」
        data_new.at[index,'平均開立張數月成長率'] = (data_new.at[index,'平均開立張數'] - data_new.at[index+1,'平均開立張數'])/data_new.at[index+1,'平均開立張數']
        data_new.at[index,'平均開立金額月成長率'] = (data_new.at[index,'平均開立金額'] - data_new.at[index+1,'平均開立金額'])/data_new.at[index+1,'平均開立金額']
        data_new.at[index,'平均客單價月成長率'] = (data_new.at[index,'平均客單價'] - data_new.at[index+1,'平均客單價'])/data_new.at[index+1,'平均客單價']

    for index in range(len(data_new2.index)-1):
        # at[資料索引值,欄位名稱]：利用資料索引值及欄位名稱來取得「單一值」
        data_new2.at[index,'平均開立張數月成長率'] = (data_new2.at[index,'平均開立張數'] - data_new2.at[index+1,'平均開立張數'])/data_new2.at[index+1,'平均開立張數']
        data_new2.at[index,'平均開立金額月成長率'] = (data_new2.at[index,'平均開立金額'] - data_new2.at[index+1,'平均開立金額'])/data_new2.at[index+1,'平均開立金額']
        data_new2.at[index,'平均客單價月成長率'] = (data_new2.at[index,'平均客單價'] - data_new2.at[index+1,'平均客單價'])/data_new2.at[index+1,'平均客單價']

    # 發票年月 轉成 yyyy-MM 型態字串 方便 plotly繪圖辨識時間
    data_new['發票年月'] = (data_new['發票年月']/100).astype('int').astype('str')+'-'+(data_new['發票年月']%100).astype('int').astype('str')

    # 發票年月 轉成 yyyy-MM 型態字串 方便 plotly繪圖辨識時間
    data_new2['發票年月'] = (data_new2['發票年月']/100).astype('int').astype('str')+'-'+(data_new2['發票年月']%100).astype('int').astype('str')

    # 開始繪圖
    fig = []
    graphJSON = []
    purpose_list = ['平均開立張數月成長率','平均開立金額月成長率','平均客單價月成長率']
    for purpose in purpose_list:
        filter_greater_than_0 = (data_new[purpose] >= 0)
        filter_lower_than_0 = (data_new[purpose] < 0)
        data_new_greater_than_0 = data_new[filter_greater_than_0]
        data_new_lower_than_0 = data_new[filter_lower_than_0]
        print(data_new_greater_than_0)
        # print(data_new_lower_than_0)

        filter_greater_than_0 = (data_new2[purpose] >= 0)
        filter_lower_than_0 = (data_new2[purpose] < 0)
        data_new2_greater_than_0 = data_new2[filter_greater_than_0]
        data_new2_lower_than_0 = data_new2[filter_lower_than_0]
        print(data_new2_greater_than_0)
        # print(data_new2_lower_than_0)


        fig1 = plotly.graph_objects.Figure()
        fig1.add_trace(plotly.graph_objects.Bar(x=data_new_greater_than_0['發票年月'],
                y=data_new_greater_than_0[purpose],
                        name=city1+' '+district1+' '+industry1+" 大於0",
                        marker_color='red'
                        ))
        fig1.add_trace(plotly.graph_objects.Bar(x=data_new_lower_than_0['發票年月'],
                y=data_new_lower_than_0[purpose],
                        name=city1+' '+district1+' '+industry1+" 小於0",
                        marker_color='green'
                        ))
        fig1.add_trace(plotly.graph_objects.Bar(x=data_new2_greater_than_0['發票年月'],
                y=data_new2_greater_than_0[purpose],
                        name=city2+' '+district2+' '+industry2+" 大於0",
                        marker_color='orange'
                        ))
        fig1.add_trace(plotly.graph_objects.Bar(x=data_new2_lower_than_0['發票年月'],
                y=data_new2_lower_than_0[purpose],
                        name=city2+' '+district2+' '+industry2+" 小於0",
                        marker_color='lime'
                        ))

        fig1.update_layout(
            title=city1+' '+district1+' '+industry1+" vs "+city2+' '+district2+' '+industry2,
            xaxis_tickfont_size=14,
            yaxis=dict(
                title=purpose,
                titlefont_size=16,
                tickfont_size=14,
            ),
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            barmode='group',
            bargap=0.15, # gap between bars of adjacent location coordinates.
            bargroupgap=0.1 # gap between bars of the same location coordinate.
        )
        # fig1.show(renderer='colab')
        graphJSON.append(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder))

    return flask.render_template("monthlyGrowthRateVS.html",graphJSON1=graphJSON[0],graphJSON2=graphJSON[1],graphJSON3=graphJSON[2],city1=city1,district1=district1,industry1=industry1,city2=city2,district2=district2,industry2=industry2)
if __name__ == "__main__":
    app1.run()
