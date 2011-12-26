# We hear about correlations every day.  Various health outcomes are
# [correlated with socioeconomic
# status](https://www.nber.org/reporter/spring03/health.html).  Iodine
# supplementation in infants is [correlated with higher
# IQ](https://www.ncbi.nlm.nih.gov/pubmed/15734706).  Models are
# everywhere as well.  An object falling for t seconds moves .5gt^2
# meters.  You can calculate correlation and built approximate models
# using several techniques, but the simplest and most popular
# technique by far is ** linear regression **.  Let's see how it
# works!
#
# <h3>County Health Rankings</h3>
#
# For our examples, we'll use the [County Health
# Rankings](http://www.countyhealthrankings.org/).  Specifically,
# we'll be looking at two datasets in this example: [Years of
# Potential Life
# Lost](https://github.com/dataiap/dataiap/blob/master/datasets/county_health_rankings/ypll.csv)
# and [Additional
# Measures](https://github.com/dataiap/dataiap/blob/master/datasets/county_health_rankings/additional_measures_cleaned.csv).
#
# [Years of potential life lost](https://en.wikipedia.org/wiki/Years_of_potential_life_lost) (YPLL) is an early mortality measure.  It
# measures, across 100,000 people, how many total of the number of
# years below the age of 75 that 100,000-person cohort loses.  For
# example, if a person dies at age 73, they contribute 2 years to this
# sum.  If they die at age 77, they contribute 0 years to the sum.
# The YPLL for each 100,000 people, averaged across counties in the
# United States is between 8000 and 9000 depending on the year.  The
# file `ypll.csv` contains per-county YPLLs for the United States in
# 2011.
#
# The additional measures (found in `additional_measures_cleaned.csv`)
# contains all sorts of fun measures per county, ranging from the
# percentage of people in the county with Diabetes to the population
# of the county.
#
# We're going to see which of the additional measures correlate
# strongly with our mortality measure, and build predictive models for
# county mortality rates given these additional measures.
#
# <h3>Loading the Rankings</h3>
# 
# The two .csv files we've given you (ypll.csv and
# additional_measures_cleaned.csv) went through quote a bit of
# scrubbing already.  You can read [our notes on the
# process](https://github.com/dataiap/dataiap/blob/master/datasets/county_health_rankings/README)
# if you're interested.
#
# There's still a bit of work to do to load the data.  Some of the
# YPLL values are marked "Unreliable" in a column ypll.csv, and we
# don't want to train our regression on these.  Simiarly, some of the
# columns of additional measures are empty, and we want to discard
# these.  Finally, there is a row per state that summarizes the
# state's statistics, and we want to ignore that row since we are
# doing a county-by-county analysis. Here's a function, `read_csv`, that
# will read the desired columns from one of the csv files.

import csv

def read_csv(file_name, cols, check_reliable):
    reader = csv.DictReader(open(file_name, 'rU'))
    rows = {} # map "statename__countyname" to the column names in cols
    for row in reader:
        if check_reliable and row['Unreliable'] == "x": # discard unreliable data
            continue
        if row['County'] == "": # ignore the first entry for each state
            continue
        rname = "%s__%s" % (row['State'], row['County'])
        try: # if a row[col] is empty, float(row[col]) throws an exception
            rows[rname] = [float(row[col]) for col in cols]
        except:
            pass
    return rows

# The function returns a dictionary mapping each state/county to the
# columns in an array `cols`.  It handles all of the dirty data: data
# marked unreliable, state-only data, and missing columns.
#
# All of this data cleaning across different .csv files will result in
# some county YPLL data to be dropped for being unreliable, and some
# county additional measures data to be dropped for having missing
# columns.  We need to do what database folks call a ** join ** between
# the two county datasets so that only the counties remaining in both
# datasets will be considered.  This is handled by the function
# `get_arrs`:

import numpy

def get_arrs(dependent_cols, independent_cols):
    ypll = read_csv("../datasets/county_health_rankings/ypll.csv", dependent_cols, True)
    measures = read_csv("../datasets/county_health_rankings/additional_measures_cleaned.csv", independent_cols, False)

    ypll_arr = []
    measures_arr = []
    for key, value in ypll.iteritems():
        if key in measures: # join ypll and measures if county is in both
            ypll_arr.append(value[0])
            measures_arr.append(measures[key])
    return (numpy.array(ypll_arr), numpy.array(measures_arr))

# We return numpy arrays (matrices) with rows corresponding to
# counties and columns corresponding to the columns we read from the
# spreadsheet.  We can finally call the `get_arrs` function to laod
# the desired columns from each file.

dependent_cols = ["YPLL Rate"]
independent_cols = ["Population", "< 18", "65 and over", "African American", "Female", "Rural", "%Diabetes" , "HIV rate", "Physical Inactivity" , "mental health provider rate", "median household income", "% high housing costs", "% Free lunch", "% child Illiteracy", "% Drive Alone"]

ypll_arr, measures_arr = get_arrs(dependent_cols, independent_cols)

# Phew.  That sucked.  Let's look at the data!

#<h3>Look at a Scatterplot</h3>
#
# Like we did during hypothesis testing, our first step is to look at
# the data to identify correlations.  The best visualization to
# identify correlations is a scatterplot, since that shows us the
# relationship between a potentially dependent variable (ypll) and an
# independent variable like % diabetes.
#
# Let's start by looking at scatterplots of ypll versus three
# potentially correlated variables: % of a community that has
# diabetes, % of the community under the age of 18, and median income.

import matplotlib.pyplot as plt

fig = plt.figure(figsize=(6, 8))

subplot = fig.add_subplot(311)
subplot.scatter(measures_arr[:,6], ypll_arr, color="#1f77b4") # 6 = diabetes
subplot.set_title("ypll vs. % of population with diabetes")

subplot = fig.add_subplot(312)
subplot.scatter(measures_arr[:,1], ypll_arr, color="#1f77b4") # 1 = age
subplot.set_title("ypll vs. % population less than 18 years of age")

subplot = fig.add_subplot(313)
subplot.scatter(measures_arr[:,10], ypll_arr, color="#1f77b4") # 10 = income
subplot.set_title("ypll vs. median household income")

plt.show()

# Your plots should look something like this:
#
#  ![YPLL vs. population with diabetes, population less than 18 years of age, and median household income](three-scatters.png)
#
# We picked these three examples because they show visual evidence of three forms of correlation:
#  * In the first plot, we can see that when the percentage of people
#  in a county with diabetes is higher so is the mortality rate
#  (YPLL)---evidence of a positive correlation.
#  * The second plot looks like a blob.  It's hard to see a
#  relationship between mortality and the fraction of people under the
#  age of 18 in a community.
#  * The final plot shows evidence of negative correlation.  Counties
#  with higher median incomes appear to have lower mortality rates.
#
# ** Exercise ** Look at scatter plots of other variables vs. YPLL.
# We found the percent of children eligible for school lunch to be
# alarmingly correlated with YPLL!
#
# <h3>Your First Regression</h3>
#
# It's time we turn the intuition from our scatterplots into math!
# We'll do this using the `ols` module, which stands for ** ordinary
# least squares ** regression.  Let's run a regression for YPLL vs. % Diabetes:

import ols

model = ols.ols(ypll_arr, measures_arr[:,6], "YPLL Rate", ["% Diabetes"]) # 6 = diabetes
print model.summary()

# As you can see, running the regression is simple, but interpreting
# the output is tougher.  Here's the output of `model.summary()` for
# the YPLL vs. % Diabetes regression:
#
#      ======================================================================  
#      Dependent Variable: YPLL Rate  
#      Method: Least Squares  
#      Date:  Fri, 23 Dec 2011  
#      
#      Time:  13:48:11
#      # obs:                2209
#      # variables:         2
#      ======================================================================
#      variable     coefficient     std. Error      t-statistic     prob.
#      ======================================================================
#      const           585.126403      169.746288      3.447064      0.000577
#      %Diabetes       782.976320      16.290678      48.062846      0.000000
#      ======================================================================
#      Models stats                         Residual stats
#      ======================================================================
#      R-squared             0.511405         Durbin-Watson stat   1.951279
#      Adjusted R-squared    0.511184         Omnibus stat         271.354997
#      F-statistic           2310.037134      Prob(Omnibus stat)   0.000000
#      Prob (F-statistic)    0.000000         JB stat              559.729657
#      Log likelihood       -19502.794993     Prob(JB)             0.000000
#      AIC criterion         17.659389        Skew                 0.752881
#      BIC criterion         17.664550        Kurtosis             4.952933
#      ======================================================================
# 
# Let's interpret this:

#   * First, let's verify the statistical significance, to make sure
#   nothing happened by chance, and that the regression is meaningful.
#   In this case, ** Prob (F-statistic) ** is something very close to
#   0, which is less than .05 or .01.  That is: we have statistical
#   significance, and we an safely interpret the rest of the data.

#   * The coefficients (called ** betas **) help us understand what
#   line best fits the data, in case we want to build a predictive
#   model.  In this case ** const ** is 585.13, and ** %Diabetes **
#   has a coefficient of 782.98.  Thus, the line (y = mx + b) that
#   best predicts YPLL from %Diabetes is: ** YPLL = (782.98 *
#   %Diabetes) + 585.13**.

#   * To understand how well the line/model we've built from the data
#   helps predict the data, we look at ** R-squared **.  This value
#   ranges from 0 (none of the change in YPLL is predicted by the
#   above equation) to 1 (100% of the change in YPLL is predicted by
#   the above equation).  In our case, 51% of the changes YPLL can be
#   predicted by a linear equation on %Diabetes.
#
# Putting this all together, we've just discovered that, without
# knowing the YPLL of a community, we can take data on the percentage
# of people affected by diabetes, and roughly reconstruct 51% of the
# YPLL's characteristics.
#
# If you want to use the information in your regression to do more
# than print a large table, you can access the data individually

#$$$

# To better visualize the model we've built, we can also plot the line
# we've calculated through the scatterplot we built before

#$$$

#
# That should result in a plot that looks something like
#
# $$$
#
# We can see that our line slopes upward (the beta coefficient in
# front of the %Diabetes term is positive) indicating a positive
# correlation.
#
# ** Exercise ** Run the correlations for percentage of population
# under 18 years of age and median household income.  We got
# statistically significant results for all of these tests.  Median
# household income does seem negatively correlated (the slope beta is
# $$$), and explains a good portion of YPLL (R-squared is $$$).
# Remember that we saw a blob in the scatterplot for percentage of
# population under 18.  The regression backs this up: the slope of $$$
# is not as strong as that of %Diabetes, and the R-squared of $$$
# suggests little predictive power of YPLL.
#
# ** Exercise ** Plot the lines calculated from the regression for
# each of these independent variables.  Do they fit the models?
#
# ** Exercise ** Run the correlation for % of children eligible for
# school lunches.  Is it significant?  Positively or negatively
# correlated?  How does this R-squared value compare to the ones we
# just calculated?
#
# <h3>Running Multiple Variables</h3>
#
# So far, we've been able to explain about 50% of the variance in YPLL
# using our additional measures data.  Can we do better?  What if we
# combine information from multiple measures?  That's called a
# multiple regression, and we already have all the tools we need to do
# it!  Let's combine household income, %Diabetes, and percentage of
# the population under 18 into one regression.
#

#$$$

# We got the following output:
#
# $$$
#
# So we're still significant, and can read the rest of the output.  A
# read of the beta coefficients suggests the best linear combination
# of all of these variables is YPLL = $$$.

# Because there are multiple independent variables in this regression,
# we should look at the Rsquare-adjusted value, which is $$$.  This
# value penalizes you for needlessly adding variables to the
# regression that don't give you more information about YPLL.  Anyway,
# check out that Rsquare---nice!  That's larger than the Rsquare value
# for any one of the regressions we ran on their own!  We can explain
# more of YPLL with these variables.
#
# ** Exercise ** Try combining other variables.  What's the largest
# adjusted Rsquare$$$(consistency on the R-Square spelling) you can
# achieve?
#<h3>Nonlinearity</h3>
#
# Is finding a bunch of independent variables and performing linear
# regression against some dependent variable the best we can do to
# model our data?  Nope!  Linear regression gives us the best line to
# fit through the data, but there are cases where the interaction
# between two variables is nonlinear.  In these cases, the scatterplots we built before matter quite a bit!
#
# Take gravity for example.  Say we measured the distance an object fell in a certain amount of time, and had a bit of noise to our measurement.  Below, we'll simulate that activity by generating the time-distance relationship that we learned in high school, but adding randomness to the measurements.
#
#$$$
# A scatterplot of the data looks like a parabola, which doesn't take
# lines very well!  We can ** transform ** this data by squaring the
# time values.
#$$$
# Here are scatterplots of the original and transformed datasets.  You
# can see that squaring the time values turned the plot into a more
# linear one.
#
# ** Exercise ** Perform a linear regression on the original and
# untransformed data.  Are they all significant?  What's the R-squared
# value of each?  Which model would you prefer?  Does the coefficient
# of the transformed value mean anything to you?
#
# ** Exercise ** Can you improve the R-squared values by
# transformation in the county health rankings?  Try taking the log of
# the population$$$, a common technique for making data that is
# bunched up spread out more.
#
# Linear regression, scatterplots, and variable transformation can get
# you a long way.  But sometimes, you just can't figure out the right
# transformation to perform even though there's a visible relationship
# in the data.  In those cases, more complex technques like [nonlinear
# regression]($$$) can fit all sorts of nonlinear functions to the
# data.
#
# <h3>Eliminate Free Lunches, Save the Planet</h3>
#
# At some point in performing a regression and testing for a
# correlation, you will be tempted to come up with solutions to
# problems the regression has not identified.  For example, we noticed
# that the percentage of children eligible for free lunch is pretty
# strongly correlated with the morbidity rate in a community.  How can
# we use this knowledge to lower the morbidity rate?
#
# ** ALERT, ALERT, ALERT!!! ** The question at the end of the last
# paragraph jumped from correlation to causation.
#
# It would be far-fetched to think that increasing or decreasing the
# number of children * eligible * for school lunches would increase or
# decrease the morbidity rate in any significant way.  What the
# correlation likely means is that there is a third variable, such as
# available healthcare, nutrition options, or overall prosperity of a
# community that is correlated with both school lunch eligibility and
# the morbidity rate.  That's a variable policymakers might have
# control over, and if we somehow improved outcomes on that third
# variable, we'd see both school lunch eligibility and the morbidity
# rate go down.
#
# Remember: correlation means two variables move together, not that
# one moves the other.
#
# <h3>ANOVA, Logistic Regression, Machine Learning</h3>
#
# Today you've swallowed quite a bit.  You learned about
# significance testing to support or reject high-likelihood meaningful
# hypotheses.  You learned about the T-Test($$$ consistency) to help
# you compare two communities on whom$$$ you've measured data.  You
# then learned about regression and correlation, for identifying
# variables that change together.  From here, there are several
# directions to grow.
#
# * A more general form of the T-Test is an [ANOVA]($$$), where you can
# identify differences among more than two groups, and control for
# known differences between items in each dataset.
#
# * [Logistic regression]($$$), and more generally
# [classification]($$$), can take a bunch of independent variables and
# map them onto binary values.  For example, you could take all of the
# additional measures for an individual and predict whether they will
# die before the age of 75.
#
#  * [Machine learning]($$$) and [Data mining]($$$) are fields that
#  assume statistical significance (you collect boatloads of data) and
#  develop algorithms to classify, cluster, and otherwise find
#  patterns in the underlying datasets.
