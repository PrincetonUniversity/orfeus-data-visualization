markdown_text_project = '''
Modern electricity markets face new sources of risk as renewables footprint increases, 
and price formation in the traditional sense will ultimately be subordinated to 
the quantification of the reliability of renewables. 

The ORFEUS platform designs a framework that allows grid operators to 
first quantify and then mitigate the risk introduced by renewables generators. 
The framework includes the following major components:

* Scenarios Generation of Load Demand and Renewables Supply 
* Simulation of Grid Operations to Generate Realistic LMPs 
* Estimation of the System Risk of Grids
* Allocation of the System Risk to Individual Generator
'''

markdown_text_scenarios = '''
Renewable energy resources reduce carbon footprint and marginal cost, but also 
introduce risk to the grid that is not fully accounted for under current operational paradigms. 
The fulcrum of the ORFEUS platform is a set of asset-specific modules which 
calibrate stochastic models of the joint behavior of forecasted and actual production, 
tailored to wind, solar and load. Models are linked through a highdimensional 
correlation constructor which renders spatial and temporal correlation structure 
tractable via LASSO-based methods and parametric representations of locational 
correlation structure (Gaussian Random Fields). 
The last figure shows examples of graphical LASSO correlation effects for NYISO 
and ERCOT zonal load forecast errors.
'''

markdown_text_simulation ='''
The ORFEUS simulation module takes the correlated asset models and produces 
large batch simulations. We focus on generating day-ahead scenarios at the 15- 
and 60-minute scale based on realistically coupled production and demand realizations 
based upon the forecasts available at run time. These simulations are critical 
inputs to existing SCUC and SCED software from which reliability cost indices 
are then constructed.
'''

markdown_text_risk = '''
Zero-marginal-cost assets are usually guaranteed to be committed even if they 
create potentially costly externalities due to uncertain production. 
The ORFEUS risk-based cost module rigorously decomposes the results of the 
simulation batch into reliability costs by asset and zone using coherent risk 
measure methodologies ensuring that system operations allocate realized costs equitably.
'''

markdown_text_commercial = '''
The ORFEUS team and Industry Advisory Board are well-positioned to deploy and 
test the platform in production settings, ultimately launching Princeton Grid 
Analytics as the commercial delivery vehicle.
'''