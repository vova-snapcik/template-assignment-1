Explanation of the code:

The data_loader file organizes raw input data which is used for the opt_model
The model is build in the opt_model
main loads data and passes to the opt_model for building the model. In the main, either assignment 1a,1b or 1c can be chosen to run and will give the solutions for every run. 
For 1a, the solutions will be for the original scenario, and the 3 ekstra scenarios created in 1av. For all of these scenarios the otimal objective and the dual variables will be printed. 
For 1b, only the optimal objective is printed, because Vlad did not finish this part. His idea was to make test for different discomfort epsilon values how it would affect the optimal price that the consumer gets. 
For 1c, the output is in the same format as it is for 1a. It prints the optimal objective and the dual variables to compare between the original and the different scenarios created.
The scenarios for a and c are created in a seperate def in the utils file: make_scenarios and make_scenarios_battery. The data is then passed to run_scenario_analysis and run_scenario_analysis_battery in the file runner, to modify data to the specific analysis. Lastly it is passed back to the opt_model to solve for the optimal solution. 

Vlad has added a 1b_interpretation.md which I (Anne) don't think is usable for any explanation, but I didn't want to delete it if he wanted to keep it as explanation of something. 