# W3go

W3go is a tool created in order to optimize your complex routing & scheduling problem.



## Problem Statement

Jon, Thomas, Laurie and Kathy want to meet somewhere. Jon wants to go to the cinema, Laurie wants to eat something but is still up with going to the cinema. Kathy and Thomas doesn't know and just want to follow the group.

Now, we have to consider:
- The four members schedules.
- The four members locations.
- The cinema and restaurant locations and open schedule.
- If anyone has a vehicule or not.
- The number of places in each vehicle.
- The rated preferences from each member for each activity. (For example, Jon would have a high rate preference on the cinema activity)

Considering all these parameters are known, what is the most efficient routing and scheduling to realize the meeting in order to minimize the distance realized by vehicles and to maximize satisfaction of each participant ?

## At a larger scale
This problem can be solved easily with common sense when there are 2, 3 or 4 participants and 2 activities (cinema & eating). But what happens when there much more participants and activities ? This become unsolvable and often creates frustration for some participant as they end up doing an activity they don't really like or out of their schedule.

An example of larger scale solution is shown below.

![image](https://user-images.githubusercontent.com/31999833/134488483-95cdab4a-970d-41cf-a408-2b461f60576f.png)

## Requirements
Solver requirements, two ways:
1) Running Mixed-Integer linear problem (MILP) locally: 
- Install a solver (gurobi, cbc, cplex)
- Edit the input data json "solver_manager" value to "local"
2) Runing MIP on a server: setup a NEOS account.
- Edit the input data json "solver_manager" value to "neos"
- Edit the input data json "neos_email" value to "your_email"

Use python 3.6.0 as the code has not been tested with other versions then pip install -r requirements.txt

## Getting started
Just run the main file, once your input json file is ready. You already have some json examples. View the results in the results folder
