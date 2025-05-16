from flask import Flask,render_template,redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy
import plotly.express as px
import pandas as pd
from datetime import datetime


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///expense.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION']=False
db=SQLAlchemy(app)

class Expense(db.Model):
   sno=db.Column(db.Integer,primary_key=True)
   Description=db.Column(db.String(100),nullable=False)
   Amount=db.Column(db.Float,nullable=False)
   Date=db.Column(db.Date,default= datetime.utcnow)

   def __repr__(self):
      return f"{self.Description} - {self.Amount}"
   
class MonthlyIncome(db.Model):
   id=db.Column(db.Integer,primary_key=True)
   income=db.Column(db.Float,nullable=False)
   date_set=db.Column(db.DateTime,default=datetime.utcnow)

   def __repr__(self):
      return f"{self.income}"


@app.route('/')
def index():
      allexpense=Expense.query.all()
      return render_template('index.html', allexpense=allexpense)

@app.route('/add',methods=['GET','POST'])
def add_expense():
   if request.method =='POST':
      desc=request.form['description']
      amt=request.form['amount']
      date_str = request.form['date']
            # Convert the date string to a datetime object
      date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

      month = date_obj.month
      year = date_obj.year

      income_entry=MonthlyIncome.query.filter_by(date_set=datetime(year,month,1)).first

      if not income_entry :
         return "You cannot add expenes for this month without setting a monthly income first."
      
       # Create the new expense record
      new_expense=Expense(Description=desc,Amount=amt,Date=date_obj)
      db.session.add(new_expense)
      db.session.commit()
      return redirect("/")
   return render_template("addexpense.html")


   

@app.route('/set',methods=['GET','POST'])
def monthly_income():
   if request.method =='POST':
      income=request.form["income"]
      month=request.form["month"]
      year=datetime.now().year
      date_set=datetime(year,int(month),1)
      new_income=MonthlyIncome(income=income,date_set=date_set)
      db.session.add(new_income)
      db.session.commit()
      return redirect("/add")
   return render_template("set_monthly.html")


@app.route('/edit/<int:sno>',methods=['GET','POST'])
def edit(sno):
   expense=Expense.query.filter_by(sno=sno).first()
   if request.method=='POST':

      desc=request.form['description']
      amt=request.form['amount']
      expense.Description=desc
      expense.Amount=float(amt)
      db.session.add(expense)
      db.session.commit()
      return redirect("/")
   
   expense=Expense.query.filter_by(sno=sno).first()
   return render_template("edit.html",expense=expense)



@app.route('/delete/<int:sno>')
def delete(sno):
   expense=Expense.query.filter_by(sno=sno).first()
   db.session.delete(expense)
   db.session.commit()
   return redirect("/")


@app.route('/dashboard')
def dashboard():
# Get all expenses
      allexpense=Expense.query.all()

# Calculate the total spend in each description
      expense_data={}
      for expense in allexpense:
         Description=expense.Description
         Amount=expense.Amount
         if Description not in expense_data:
            expense_data[Description] = 0
         expense_data[Description] += Amount

      Descriptions = list(expense_data.keys())
      Amounts = list(expense_data.values())

# Create Bar Chart for Expenses by Description
      fig_expense=px.bar(
         x=Descriptions,
         y=Amounts,
         labels={"x":"Description","y":"Amount"},
         title="Expense by Decription"
)
      
          # Time Series Line Chart (Expenses Over Time)
      expense_dates=[expense.Date for expense in allexpense]
      expense_amounts=[expense.Amount for expense in allexpense]

      fig_line=px.line(
         x=expense_dates,
         y=expense_amounts,
         title="Expenses over Time",
         labels={"x":"Date","y":"Expense Amount"}
      )

      monthly_income_record=MonthlyIncome.query.order_by(MonthlyIncome.date_set.desc()).first()
      if monthly_income_record:
         monthly_income=monthly_income_record.income
         total_expense=sum(Amounts)
         savings = monthly_income- total_expense  
      
      else:
         monthly_income = 0
         total_expense = 0
         savings = 0
         # Create pie chart for Utilized vs Saving
      pie_data = { "Utilized":total_expense ,"saved":savings}
      fig_pie=px.pie(
         names=list(pie_data.keys()),
         values=list(pie_data.values()),
         title="Utilized VS Savings"
      )
      
      
       # Convert the figures to HTML
      bar_chart_html = fig_expense.to_html(full_html=False)
      line_chart_html = fig_line.to_html(full_html=False)
      pie_chart_html = fig_pie.to_html(full_html=False)
# Render the dashboard with total expenditure and balance
      return render_template(
        'dashboard.html', 
      bar_chart_html = bar_chart_html,
      line_chart_html = line_chart_html,
      pie_chart_html = pie_chart_html,
      total_expense = total_expense,
      savings=savings,
      monthly_income=monthly_income
    )
if __name__== ("__main__"):
   
    with app.app_context():
     db.create_all()

    app.run(debug=True)

 