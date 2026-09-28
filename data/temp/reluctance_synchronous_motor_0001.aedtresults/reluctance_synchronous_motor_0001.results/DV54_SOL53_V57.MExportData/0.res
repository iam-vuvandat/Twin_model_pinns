      SYNCHRONOUS RELUCTANCE MOTOR DESIGN

                      File: Setup1.res

     GENERAL DATA

Operation Type:	Motor
Source Type:	AC
Rated Output Power (kW):	3
Rated Power Factor:	0.8
Capacitive Power Factor:	No
Frequency (Hz):	250
Rated Voltage (V):	300
Load Type:	Const Speed
Rated Speed (rpm):	3000
Operating Temperature (C):	60

     STATOR DATA 

Stator Core Type:	SLOT_AC
Stator Position:	Outer
Number of Poles:	10
Outer Diameter of Stator (mm):  	150
Inner Diameter of Stator (mm):  	70
Length of Stator Core (mm):  	70
Stacking Factor of Stator Core:	0.95
Steel Type of Stator:	steel_1008

Number of Stator Slots:	15
Type of Stator Slot:	1
Stator Slot	
            hs0 (mm):  	1
            hs2 (mm):  	1
            bs0 (mm):  	1
            bs1 (mm):  	1
            bs2 (mm):  	1
Top Tooth Width (mm):  	13.99
Bottom Tooth Width (mm):  	14.4058

     STATOR WINDING DATA 

Number of Phases:	3
Winding Connection:	Y3
Number of Parallel Branches:	1
Number of Layers:	2
Winding Type:	Whole Coiled
Coil Pitch:	1
Winding Factor:	0.866025

Number of Conductors per Slot:	10
Number of Wires per Conductor:	1
Wire Diameter (mm):  	0.0198
Wire Wrap Thickness (mm):  	1

Wedge Thickness (mm):  	0
Slot Liner Thickness (mm):  	0
Layer Insulation (mm):  	0
Slot Area (mm^2):	2.3927
Net Slot Area (mm^2):	1.3927
Slot Fill Factor (%):	746.746
Limited Slot Fill Factor (%):	75
**** Warning - Result is Unfeasable ****
  Slot Fill Factor is beyond its limited value.

Coil Half-Turn Length (mm):  	84.9288
End Length Adjustment (mm):  	0
End-Coil Clearance (mm):  	0
Conductor Type of Stator:	copper
Conductor Resistivity at 75C (ohm.mm^2/m):	0.020797

     ROTOR DATA 

Rotor Core Type:	NONS_RELU
Rotor Position:	Inner
Number of Poles:	10
Outer Diameter of Rotor (mm):  	69
Inner Diameter of Rotor (mm):  	20

Length of Rotor Core (mm):  	70
Stacking Factor of Rotor Core:	1
Steel Type of Rotor:	steel_1008

Rotor Pole Type:	4
Rotor Pole Dimensions:	
        Barriers:	2
        H (mm):  	2
        W (mm):  	2
        R (mm):  	0.20218
        R0 (mm):  	1
        Rb (mm):  	15
        B0 (mm):  	2
        Y0 (mm):  	2

     SHAFT DATA 

Magnetic Shaft:	No
Friction Loss (W):	1
Windage Loss/Power (W):	1
Reference Speed (rpm):	3000

     MATERIAL CONSUMPTION

Stator Wire Density (kg/m^3):  	8933
Stator Core Steel Density (kg/m^3):  	7872
Rotor Magnet Density (kg/m^3):  	7800
Rotor Core Steel Density (kg/m^3):  	7872

Stator Copper Weight (kg):  	3.504e-05
Stator Core Steel Weight (kg):  	7.21739
Rotor Core Steel Weight (kg):  	1.63961
Rotor Magnet Weight (kg):  	0
Stator Net Weight (kg):  	7.21743
Rotor Net Weight (kg):  	1.63961

Stator Core Steel Consumption (kg):  	12.2543
Rotor Core Steel Consumption (kg):  	2.85659

     UNSATURATED PARAMETERS

Stator Resistance R1 (ohm):	272.939
Stator Resistance at 20C (ohm):	235.93
Stator Leakage Inductance L1 (H):	0.000139231
  Slot Leakage Inductance Ls1 (H):	3.33083e-05
  End Leakage Inductance Le1 (H):	4.90682e-06
  Spread Harmonic Inductance Ld1 (H):	8.43618e-05
  Muture Slot Leakage Inductance Lsm (H):	-1.66542e-05
Uniform Air-gap Magnetizing Inductance Lm (H):	0.000213863
D-axis Armature Reactive Inductance Lad (H):	0.000210291
Q-axis Armature Reactive Inductance Laq (H):	0.000198355
D-axis Armature synchronous Inductance Ld (H):	0.000349522
Q-axis Armature synchronous Inductance Lq (H):	0.000337586

     NO-LOAD MAGNETIC DATA

Stator Tooth Flux Density (Tesla):	0.00583588
Stator Yoke Flux Density (Tesla):	0.000357429
Rotor Top-Tooth Flux Density (Tesla):	0.001532
Rotor Yoke Flux Density (Tesla):	0.00104102
Air-Gap Flux Density (Tesla):	0.00512615

Stator Tooth Ampere Turns (A.T):	0.00923734
Stator Yoke Ampere Turns (A.T):	0.00389939
Rotor Top-Tooth Ampere Turns (A.T):	0.0201956
Rotor Yoke Ampere Turns (A.T):	0.00213212
Air-Gap Ampere Turns (A.T):	2.08791
Total Ampere Turn Drop (A.T):	2.12337
Saturation Factor:	1.01699

Correction Factor for Magnetic	
  Circuit Length of Stator Yoke:	0.40313
Correction Factor for Magnetic	
  Circuit Length of Rotor Yoke:	1

     FULL-LOAD ELECTRIC DATA

Root-Mean-Square Armature Current (A):	0.634573
Armature Thermal Load (A^2/mm^3):	898.462
Specific Electric Loading (A/mm):	0.435952
Armature Current Density (A/mm^2):	2060.92
Frictional and Windage Loss (W):	2
Iron-Core Loss (W):	0
Armature Copper Loss (W):	329.724
Transistor Loss (W):	0
Diode Loss (W):	0
Total Loss (W):	331.724
Output Power (W):	-1.99996
Input Power (W):	329.724
Power Factor:	0.999941
Efficiency (%):	0

Torque Angle (deg):	0
Current Lag Angle (deg):	0.105867
Rated Speed (rpm):	3000
Rated Torque (N.m):	-0.00636607

     TRANSIENT FEA INPUT DATA 

For Stator Winding:
  Number of Turns:	25
  Parallel Branches:	1
  Terminal Resistance (ohm):	272.939
  End Leakage Inductance (H):	4.90682e-06
2D Equivalent Value:
  Equivalent Model Depth (mm):  	70
  Equivalent Stator Stacking Factor:	0.95
  Equivalent Rotor Stacking Factor:	1
