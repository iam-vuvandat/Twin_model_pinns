' ----------------------------------------------------------------------
' Script Created by RMxprt to generate Maxwell 2D/3D                    
' Can specify one arg to setup external circuit                         
' ----------------------------------------------------------------------

Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
Set oArgs = AnsoftScript.arguments
Set oDesktop = oAnsoftApp.GetAppDesktop()
oDesktop.RestoreWindow 
Enable = oDesktop.GetAutoSaveEnabled()
oDesktop.EnableAutoSave False
Set oProject = oDesktop.GetActiveProject()
if (oArgs.Count > 0) then 
Set oDesign = oProject.GetDesign(oArgs(0))
else 
Set oDesign = oProject.GetActiveDesign()
end if
designName = oDesign.GetName 
Set oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.SetModelUnits Array("NAME:Units Parameter", "Units:=", "mm", _
  "Rescale:=", False)
oDesign.SetSolutionType "Transient"
Set oModule = oDesign.GetModule("BoundarySetup")
oEditor.SetModelValidationSettings Array("NAME:Validation Options", _
  "EntityCheckLevel:=", "Strict", "IgnoreUnclassifiedObjects:=", True)
oDesign.SetDesignSettings Array("NAME:Design Settings Data", _
  "InsulatorThreshold:=", 2500000)
On Error Resume Next
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array(_
  "NAME:fractions", "PropType:=", "VariableProp", "UserDef:=", True, _
  "Value:=", "5"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:ChangedProps", _
  Array("NAME:fractions", "Value:=", "5"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array(_
  "NAME:halfAxial", "PropType:=", "VariableProp", "UserDef:=", True, _
  "Value:=", "0"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:ChangedProps", _
  Array("NAME:halfAxial", "Value:=", "0"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array(_
  "NAME:endRegion", "PropType:=", "VariableProp", "UserDef:=", True, _
  "Value:=", "7.4644078476683466mm"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:ChangedProps", _
  Array("NAME:endRegion", "Value:=", "7.4644078476683466mm"))))
On Error Goto 0
Set oDefinitionManager = oProject.GetDefinitionManager()
oDefinitionManager.ModifyLibraries designName, Array("NAME:PersonalLib"), _
  Array("NAME:UserLib"), Array("NAME:SystemLib", "Materials:=", Array(_
  "Materials", "RMxprt"))
On Error Resume Next
Set oModule = oDesign.GetModule("AnalysisSetup")
oModule.DeleteSetups Array("Setup1")
Set oModule = oDesign.GetModule("ModelSetup")
oModule.DeleteMotionSetup Array("MotionSetup1")
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.DeleteBoundaries Array("Independent1")
oModule.DeleteBoundaries Array("Dependent1")
oModule.DeleteBoundaries Array("PhaseA")
oModule.DeleteBoundaries Array("PhaseB")
oModule.DeleteBoundaries Array("PhaseC")
oEditor.Delete Array("NAME:Selections", "Selections:=", "Band")
oEditor.Delete Array("NAME:Selections", "Selections:=", "InnerRegion")
oEditor.Delete Array("NAME:Selections", "Selections:=", "OuterRegion")
oEditor.Delete Array("NAME:Selections", "Selections:=", "StatorRegion")
oEditor.Delete Array("NAME:Selections", "Selections:=", "IndependentSheet")
oEditor.Delete Array("NAME:Selections", "Selections:=", "DependentSheet")
On Error Goto 0
_
  if (oDefinitionManager.DoesMaterialExist("steel_1008_3DSF0.950")  = False) then
oDefinitionManager.AddMaterial Array("NAME:steel_1008_3DSF0.950", _
  "CoordinateSystemType:=", "Cartesian", Array("NAME:AttachedData"), Array(_
  "NAME:ModifierData"), Array("NAME:permeability", "property_type:=", _
  "nonlinear", "HUnit:=", "A_per_meter", "BUnit:=", "tesla", Array(_
  "NAME:BHCoordinates", Array("NAME:Coordinate", "X:=", 0, "Y:=", 0), Array(_
  "NAME:Coordinate", "X:=", 159.2, "Y:=", 0.2402), Array("NAME:Coordinate", _
  "X:=", 318.3, "Y:=", 0.8654), Array("NAME:Coordinate", "X:=", 477.5, "Y:="_
  , 1.1106), Array("NAME:Coordinate", "X:=", 636.6, "Y:=", 1.2458), Array(_
  "NAME:Coordinate", "X:=", 795.8, "Y:=", 1.331), Array("NAME:Coordinate", _
  "X:=", 1591.5, "Y:=", 1.5), Array("NAME:Coordinate", "X:=", 3183.1, "Y:=", _
  1.6), Array("NAME:Coordinate", "X:=", 4774.6, "Y:=", 1.683), Array(_
  "NAME:Coordinate", "X:=", 6366.2, "Y:=", 1.741), Array("NAME:Coordinate", _
  "X:=", 7957.7, "Y:=", 1.78), Array("NAME:Coordinate", "X:=", 15915.5, "Y:="_
  , 1.905), Array("NAME:Coordinate", "X:=", 31831, "Y:=", 2.025), Array(_
  "NAME:Coordinate", "X:=", 47746.5, "Y:=", 2.085), Array("NAME:Coordinate", _
  "X:=", 63662, "Y:=", 2.13), Array("NAME:Coordinate", "X:=", 79577.5, "Y:="_
  , 2.165), Array("NAME:Coordinate", "X:=", 159155, "Y:=", 2.28), Array(_
  "NAME:Coordinate", "X:=", 318310, "Y:=", 2.485), Array("NAME:Coordinate", _
  "X:=", 397887, "Y:=", 2.5851), Array("NAME:Coordinate", "X:=", 1193657, _
  "Y:=", 3.5861))), Array("NAME:magnetic_coercivity", "property_type:=", _
  "VectorProperty", "Magnitude:=", "0A_per_meter", "DirComp1:=", "0", _
  "DirComp2:=", "0", "DirComp3:=", "0"), "conductivity:=", 2000000, _
  "mass_density:=", 7872, Array("NAME:stacking_type", "property_type:=", _
  "ChoiceProperty", "Choice:=", "Lamination"), "stacking_factor:=", "0.95", _
  Array("NAME:stacking_direction", "property_type:=", "ChoiceProperty", _
  "Choice:=", "V(3)"))
end if
if (oDefinitionManager.DoesMaterialExist("steel_1008")  = False) then
oDefinitionManager.AddMaterial Array("NAME:steel_1008", _
  "CoordinateSystemType:=", "Cartesian", Array("NAME:AttachedData"), Array(_
  "NAME:ModifierData"), Array("NAME:permeability", "property_type:=", _
  "nonlinear", "HUnit:=", "A_per_meter", "BUnit:=", "tesla", Array(_
  "NAME:BHCoordinates", Array("NAME:Coordinate", "X:=", 0, "Y:=", 0), Array(_
  "NAME:Coordinate", "X:=", 159.2, "Y:=", 0.2402), Array("NAME:Coordinate", _
  "X:=", 318.3, "Y:=", 0.8654), Array("NAME:Coordinate", "X:=", 477.5, "Y:="_
  , 1.1106), Array("NAME:Coordinate", "X:=", 636.6, "Y:=", 1.2458), Array(_
  "NAME:Coordinate", "X:=", 795.8, "Y:=", 1.331), Array("NAME:Coordinate", _
  "X:=", 1591.5, "Y:=", 1.5), Array("NAME:Coordinate", "X:=", 3183.1, "Y:=", _
  1.6), Array("NAME:Coordinate", "X:=", 4774.6, "Y:=", 1.683), Array(_
  "NAME:Coordinate", "X:=", 6366.2, "Y:=", 1.741), Array("NAME:Coordinate", _
  "X:=", 7957.7, "Y:=", 1.78), Array("NAME:Coordinate", "X:=", 15915.5, "Y:="_
  , 1.905), Array("NAME:Coordinate", "X:=", 31831, "Y:=", 2.025), Array(_
  "NAME:Coordinate", "X:=", 47746.5, "Y:=", 2.085), Array("NAME:Coordinate", _
  "X:=", 63662, "Y:=", 2.13), Array("NAME:Coordinate", "X:=", 79577.5, "Y:="_
  , 2.165), Array("NAME:Coordinate", "X:=", 159155, "Y:=", 2.28), Array(_
  "NAME:Coordinate", "X:=", 318310, "Y:=", 2.485), Array("NAME:Coordinate", _
  "X:=", 397887, "Y:=", 2.5851), Array("NAME:Coordinate", "X:=", 1193657, _
  "Y:=", 3.5861))), Array("NAME:magnetic_coercivity", "property_type:=", _
  "VectorProperty", "Magnitude:=", "0A_per_meter", "DirComp1:=", "0", _
  "DirComp2:=", "0", "DirComp3:=", "0"), "conductivity:=", 2000000, _
  "mass_density:=", 7872) 
end if
if (oDefinitionManager.DoesMaterialExist("copper_60C")  = False) then
oDefinitionManager.AddMaterial Array("NAME:copper_60C", _
  "CoordinateSystemType:=", "Cartesian", Array("NAME:AttachedData"), Array(_
  "NAME:ModifierData"), "conductivity:=", "58000000")
end if
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/Band", "Version:=", "12.1", "NoOfParameters:=", 7, _
  "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69.5mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "20mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "84.9288156953367mm"), Array("NAME:Pair", "Name:=", "SegAngle", _
  "Value:=", "0deg"), Array("NAME:Pair", "Name:=", "Fractions", "Value:=", _
  "1"), Array("NAME:Pair", "Name:=", "HalfAxial", "Value:=", "0"), Array(_
  "NAME:Pair", "Name:=", "InfoCore", "Value:=", "100"))), Array(_
  "NAME:Attributes", "Name:=", "Shaft", "Flags:=", "", "Color:=", _
  "(0 255 255)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "vacuum", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/Band", "Version:=", "12.1", "NoOfParameters:=", 7, _
  "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69.5mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "84.9288156953367mm"), Array("NAME:Pair", "Name:=", "SegAngle", _
  "Value:=", "0deg"), Array("NAME:Pair", "Name:=", "Fractions", "Value:=", _
  "5"), Array("NAME:Pair", "Name:=", "HalfAxial", "Value:=", "0"), Array(_
  "NAME:Pair", "Name:=", "InfoCore", "Value:=", "100"))), Array(_
  "NAME:Attributes", "Name:=", "OuterRegion", "Flags:=", "", "Color:=", _
  "(0 255 255)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "vacuum", "SolveInside:=", True) 
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "OuterRegion:CreateUserDefinedPart:1", "Fractions", "fractions"
On Error Resume Next
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "OuterRegion:CreateUserDefinedPart:1", "HalfAxial", "halfAxial"
On Error Goto 0
oEditor.Copy Array("NAME:Selections", "Selections:=", "OuterRegion")
oEditor.Paste
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "OuterRegion1:CreateUserDefinedPart:1", "InfoCore", "2"
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "OuterRegion1"), _
  Array("NAME:ChangedProps", Array("NAME:Name", "Value:=", "IndependentSheet"_
  ))))
oEditor.Copy Array("NAME:Selections", "Selections:=", "IndependentSheet")
oEditor.Paste
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "IndependentSheet1:CreateUserDefinedPart:1", "InfoCore", "3"
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", _
  "IndependentSheet1"), Array("NAME:ChangedProps", Array("NAME:Name", _
  "Value:=", "DependentSheet"))))
oEditor.Copy Array("NAME:Selections", "Selections:=", "OuterRegion")
oEditor.Paste
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "OuterRegion1:CreateUserDefinedPart:1", "InfoCore", "1"
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "OuterRegion1"), _
  Array("NAME:ChangedProps", Array("NAME:Name", "Value:=", "Tool"))))
tool = oEditor.GetBodyNamesByPosition(Array("NAME:Parameters", "XPosition:=", _
  "78.75mm", "YPosition:=", "0mm", "ZPosition:=", "0mm"))
oEditor.FitAll 
Set oModule = oDesign.GetModule("ModelSetup")
oModule.SetSymmetryMultiplier "fractions*(1+halfAxial)"
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignMaster Array("NAME:Independent1", "Objects:=", Array(_
  "IndependentSheet"), Array("NAME:CoordSysVector", "Origin:=", Array("0mm", _
  "0mm", "0mm"), "UPos:=", Array("75mm", "0mm", "0mm")), "ReverseV:=", True)
oModule.AssignSlave Array("NAME:Dependent1", "Objects:=", Array(_
  "DependentSheet"), Array("NAME:CoordSysVector", "Origin:=", Array("0mm", _
  "0mm", "0mm"), "UPos:=", Array("23.17627457812106mm", _
  "71.329238722136509mm", "0mm")), "ReverseV:=", True, "Master:=", _
  "Independent1", "RelationIsSame:=", True)
Set oModule = oDesign.GetModule("AnalysisSetup")
oModule.InsertSetup "Transient", Array("NAME:Setup1", "StopTime:=", "0.008s", _
  "TimeStep:=", "4e-05s")
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.SetMinimumTimeStep "0.0004ms" 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SlotCore", "Version:=", "12.1", "NoOfParameters:=", 19_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "70mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
  ), Array("NAME:Pair", "Name:=", "Slots", "Value:=", "15"), Array(_
  "NAME:Pair", "Name:=", "SlotType", "Value:=", "1"), Array("NAME:Pair", _
  "Name:=", "Hs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Hs01", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Hs1", "Value:=", "0mm"), _
  Array("NAME:Pair", "Name:=", "Hs2", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Bs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs1", _
  "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs2", "Value:=", "1mm"), _
  Array("NAME:Pair", "Name:=", "Rs", "Value:=", "0.5mm"), Array("NAME:Pair", _
  "Name:=", "FilletType", "Value:=", "0"), Array("NAME:Pair", "Name:=", _
  "HalfSlot", "Value:=", "0"), Array("NAME:Pair", "Name:=", "SegAngle", _
  "Value:=", "30deg"), Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", _
  "84.9288156953367mm"), Array("NAME:Pair", "Name:=", "InfoCore", "Value:=", _
  "0"))), Array("NAME:Attributes", "Name:=", "Stator", "Flags:=", "", _
  "Color:=", "(132 132 193)", "Transparency:=", 0, "PartCoordinateSystem:=", _
  "Global", "MaterialName:=", "steel_1008_3DSF0.950", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SlotCore", "Version:=", "12.1", "NoOfParameters:=", 19_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "70mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
  ), Array("NAME:Pair", "Name:=", "Slots", "Value:=", "15"), Array(_
  "NAME:Pair", "Name:=", "SlotType", "Value:=", "1"), Array("NAME:Pair", _
  "Name:=", "Hs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Hs01", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Hs1", "Value:=", "0mm"), _
  Array("NAME:Pair", "Name:=", "Hs2", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Bs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs1", _
  "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs2", "Value:=", "1mm"), _
  Array("NAME:Pair", "Name:=", "Rs", "Value:=", "0.5mm"), Array("NAME:Pair", _
  "Name:=", "FilletType", "Value:=", "0"), Array("NAME:Pair", "Name:=", _
  "HalfSlot", "Value:=", "0"), Array("NAME:Pair", "Name:=", "SegAngle", _
  "Value:=", "30deg"), Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", _
  "84.9288156953367mm"), Array("NAME:Pair", "Name:=", "InfoCore", "Value:=", _
  "1"))), Array("NAME:Attributes", "Name:=", "StatorSlotInsu", "Flags:=", ""_
  , "Color:=", "(132 132 193)", "Transparency:=", 0, "PartCoordinateSystem:="_
  , "Global", "MaterialName:=", "vacuum", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/LapCoil", "Version:=", "16.0", "NoOfParameters:=", 22_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "70mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
  ), Array("NAME:Pair", "Name:=", "Slots", "Value:=", "15"), Array(_
  "NAME:Pair", "Name:=", "SlotType", "Value:=", "1"), Array("NAME:Pair", _
  "Name:=", "Hs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Hs1", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Hs2", "Value:=", "1mm"), _
  Array("NAME:Pair", "Name:=", "Bs0", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Bs1", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs2", _
  "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Rs", "Value:=", "0.5mm"), _
  Array("NAME:Pair", "Name:=", "FilletType", "Value:=", "0"), Array(_
  "NAME:Pair", "Name:=", "Layers", "Value:=", "2"), Array("NAME:Pair", _
  "Name:=", "CoilPitch", "Value:=", "-1"), Array("NAME:Pair", "Name:=", _
  "EndExt", "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SpanExt", _
  "Value:=", "0.1mm"), Array("NAME:Pair", "Name:=", "BendAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", "10deg"), _
  Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", "84.9288156953367mm"_
  ), Array("NAME:Pair", "Name:=", "InfoCoil", "Value:=", "1"))), Array(_
  "NAME:Attributes", "Name:=", "Coil", "Flags:=", "", "Color:=", _
  "(250 167 14)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "copper_60C", "SolveInside:=", True) 
oEditor.DuplicateAroundAxis Array("NAME:Selections", "Selections:=", "Coil"), _
  Array("NAME:DuplicateAroundAxisParameters", "CoordinateSystemID:=", -1, _
  "CreateNewObjects:=", True, "WhichAxis:=", "Z", "AngleStr:=", "24deg", _
  "NumClones:=", "15"), Array("NAME:Options", "DuplicateBoundaries:=", False)
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Coil"), Array(_
  "NAME:ChangedProps", Array("NAME:Name", "Value:=", "Coil_0"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Coil_0", "Coil_3"_
  , "Coil_6", "Coil_9", "Coil_12"), Array("NAME:ChangedProps", Array(_
  "NAME:Color", "R:=", 255, "G:=", 0, "B:=", 0))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Coil_1", "Coil_4"_
  , "Coil_7", "Coil_10", "Coil_13"), Array("NAME:ChangedProps", Array(_
  "NAME:Color", "R:=", 0, "G:=", 128, "B:=", 0))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Coil_2", "Coil_5"_
  , "Coil_8", "Coil_11", "Coil_14"), Array("NAME:ChangedProps", Array(_
  "NAME:Color", "R:=", 0, "G:=", 0, "B:=", 255))))
On Error Resume Next
oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "StatorSlotInsu", _
  "Tool Parts:=", "Coil_0,Coil_1,Coil_2,Coil_3,Coil_4,Coil_5,Coil_6,Coil_7" & _
  ",Coil_8,Coil_9,Coil_10,Coil_11,Coil_12,Coil_13,Coil_14"), Array(_
  "NAME:SubtractParameters", "CoordinateSystemID:=", -1, "KeepOriginals:=", _
  True)
oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "StatorSlotInsu", _
  "Tool Parts:=", "Stator"), Array("NAME:SubtractParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", True)
oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "StatorSlotInsu", _
  "Tool Parts:=", "Tool"), Array("NAME:SubtractParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", True)
On Error Goto 0
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SynRMCore", "Version:=", "12.0", "NoOfParameters:=", _
  15, "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "20mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "70mm"), Array("NAME:Pair", "Name:=", "Poles", "Value:=", "10"_
  ), Array("NAME:Pair", "Name:=", "PoleType", "Value:=", "4"), Array(_
  "NAME:Pair", "Name:=", "Barriers", "Value:=", "2"), Array("NAME:Pair", _
  "Name:=", "H", "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "W", _
  "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "R", "Value:=", _
  "0.2021804002172839mm"), Array("NAME:Pair", "Name:=", "R0", "Value:=", _
  "1mm"), Array("NAME:Pair", "Name:=", "Rb", "Value:=", "15mm"), Array(_
  "NAME:Pair", "Name:=", "Y0", "Value:=", "2mm"), Array("NAME:Pair", "Name:="_
  , "B0", "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "LenRegion", _
  "Value:=", "84.9288156953367mm"), Array("NAME:Pair", "Name:=", "InfoCore", _
  "Value:=", "0"))), Array("NAME:Attributes", "Name:=", "Rotor", "Flags:=", _
  "", "Color:=", "(132 132 193)", "Transparency:=", 0, _
  "PartCoordinateSystem:=", "Global", "MaterialName:=", "steel_1008", _
  "SolveInside:=", True) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "OuterRegion", _
  "IndependentSheet", "DependentSheet"), Array("NAME:ChangedProps", Array(_
  "NAME:Transparent", "Value:=", 0.75))))
oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "Shaft,Stator,Coil_0" & _
  ",Coil_1,Coil_2,Coil_3,Coil_4,Coil_5,Coil_6,Coil_7,Coil_8,Coil_9,Coil_10" & _
  ",Coil_11,Coil_12,Coil_13,Coil_14,Rotor", "Tool Parts:=", tool(0)), _
  Array("NAME:SubtractParameters", "CoordinateSystemID:=", -1, _
  "KeepOriginals:=", False)
oEditor.FitAll 
Set oModule = oDesign.GetModule("AnalysisSetup")
oModule.EditSetup "Setup1", Array("NAME:Setup1", "StopTime:=", "0.04s")
if (Enable > 0) then 
oDesktop.EnableAutoSave True
end if
