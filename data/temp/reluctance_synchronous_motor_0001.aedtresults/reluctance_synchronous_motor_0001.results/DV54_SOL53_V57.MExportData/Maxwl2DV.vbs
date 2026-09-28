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
Set oDesign = oProject.GetActiveDesign()
designName = oDesign.GetName 
Set oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.SetModelUnits Array("NAME:Units Parameter", "Units:=", "mm", _
  "Rescale:=", False)
oDesign.SetSolutionType "Transient", "XY"
Set oModule = oDesign.GetModule("BoundarySetup")
if (oArgs.Count = 1) then 
oModule.EditExternalCircuit oArgs(0), Array(), Array(), Array(), Array()
end if
oEditor.SetModelValidationSettings Array("NAME:Validation Options", _
  "EntityCheckLevel:=", "Strict", "IgnoreUnclassifiedObjects:=", True)
On Error Resume Next
Set oModule = oDesign.GetModule("MeshSetup")
oModule.InitialMeshSettings Array("NAME:MeshSettings", "MeshMethod:=", _
  "AnsoftTAU")
On Error Goto 0
On Error Resume Next
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array(_
  "NAME:fractions", "PropType:=", "VariableProp", "UserDef:=", True, _
  "Value:=", "5"))))
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:ChangedProps", _
  Array("NAME:fractions", "Value:=", "5"))))
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
  if (oDefinitionManager.DoesMaterialExist("steel_1008_2DSF0.950")  = False) then
oDefinitionManager.AddMaterial Array("NAME:steel_1008_2DSF0.950", _
  "CoordinateSystemType:=", "Cartesian", Array("NAME:AttachedData"), Array(_
  "NAME:ModifierData"), Array("NAME:permeability", "property_type:=", _
  "nonlinear", "HUnit:=", "A_per_meter", "BUnit:=", "tesla", Array(_
  "NAME:BHCoordinates", Array("NAME:Coordinate", "X:=", 0, "Y:=", 0), Array(_
  "NAME:Coordinate", "X:=", 159.2, "Y:=", 0.2282), Array("NAME:Coordinate", _
  "X:=", 318.3, "Y:=", 0.82215), Array("NAME:Coordinate", "X:=", 477.5, "Y:="_
  , 1.0551), Array("NAME:Coordinate", "X:=", 636.6, "Y:=", 1.18355), Array(_
  "NAME:Coordinate", "X:=", 795.8, "Y:=", 1.2645), Array("NAME:Coordinate", _
  "X:=", 1591.5, "Y:=", 1.4251), Array("NAME:Coordinate", "X:=", 3183.1, _
  "Y:=", 1.5202), Array("NAME:Coordinate", "X:=", 4774.6, "Y:=", 1.59915), _
  Array("NAME:Coordinate", "X:=", 6366.2, "Y:=", 1.65435), Array(_
  "NAME:Coordinate", "X:=", 7957.7, "Y:=", 1.6915), Array("NAME:Coordinate", _
  "X:=", 15915.5, "Y:=", 1.81075), Array("NAME:Coordinate", "X:=", 31831, _
  "Y:=", 1.92575), Array("NAME:Coordinate", "X:=", 47746.5, "Y:=", 1.98375), _
  Array("NAME:Coordinate", "X:=", 63662, "Y:=", 2.0275), Array(_
  "NAME:Coordinate", "X:=", 79577.5, "Y:=", 2.06175), Array("NAME:Coordinate"_
  , "X:=", 159155, "Y:=", 2.176), Array("NAME:Coordinate", "X:=", 318310, _
  "Y:=", 2.38075), Array("NAME:Coordinate", "X:=", 397887, "Y:=", 2.480845), _
  Array("NAME:Coordinate", "X:=", 1193657, "Y:=", 3.4817947))), Array(_
  "NAME:magnetic_coercivity", "property_type:=", "VectorProperty", _
  "Magnitude:=", "0A_per_meter", "DirComp1:=", "0", "DirComp2:=", "0", _
  "DirComp3:=", "0"), "conductivity:=", 2000000, "mass_density:=", 7478.4) 
end if
_
  if (oDefinitionManager.DoesMaterialExist("steel_1008_2DSF1.000")  = False) then
oDefinitionManager.AddMaterial Array("NAME:steel_1008_2DSF1.000", _
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
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "Fractions", "Value:=", "1"), Array(_
  "NAME:Pair", "Name:=", "HalfAxial", "Value:=", "0"), Array("NAME:Pair", _
  "Name:=", "InfoCore", "Value:=", "0"))), Array("NAME:Attributes", "Name:="_
  , "Band", "Flags:=", "", "Color:=", "(0 255 255)", "Transparency:=", 0, _
  "PartCoordinateSystem:=", "Global", "MaterialName:=", "vacuum", _
  "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/Band", "Version:=", "12.1", "NoOfParameters:=", 7, _
  "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69.5mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "20mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "Fractions", "Value:=", "1"), Array(_
  "NAME:Pair", "Name:=", "HalfAxial", "Value:=", "0"), Array("NAME:Pair", _
  "Name:=", "InfoCore", "Value:=", "100"))), Array("NAME:Attributes", _
  "Name:=", "Shaft", "Flags:=", "", "Color:=", "(0 255 255)", _
  "Transparency:=", 0, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
  "vacuum", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/Band", "Version:=", "12.1", "NoOfParameters:=", 7, _
  "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69.5mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "Fractions", "Value:=", "5"), Array(_
  "NAME:Pair", "Name:=", "HalfAxial", "Value:=", "0"), Array("NAME:Pair", _
  "Name:=", "InfoCore", "Value:=", "100"))), Array("NAME:Attributes", _
  "Name:=", "OuterRegion", "Flags:=", "", "Color:=", "(0 255 255)", _
  "Transparency:=", 0, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
  "vacuum", "SolveInside:=", True) 
oEditor.SetPropertyValue "Geometry3DCmdTab", _
  "OuterRegion:CreateUserDefinedPart:1", "Fractions", "fractions"
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
oModule.SetSymmetryMultiplier "fractions"
Set oModule = oDesign.GetModule("BoundarySetup")
edgeID = oEditor.GetEdgeByPosition(Array("NAME:Parameters", "BodyName:=", _
  "OuterRegion", "XPosition:=", "60.67627457812106mm", "YPosition:=", _
  "44.083893921935484mm", "ZPosition:=", "0mm"))
oModule.AssignVectorPotential Array("NAME:VectorPotential1", "Edges:="_
  , Array(edgeID), "Value:=", "0", "CoordinateSystem:=", "")
edgeID = oEditor.GetEdgeByPosition(Array("NAME:Parameters", "BodyName:=", _
  "OuterRegion", "XPosition:=", "37.5mm", "YPosition:=", "0mm", "ZPosition:="_
  , "0mm"))
oModule.AssignMaster Array("NAME:Independent1", "Edges:=", Array(edgeID), _
  "ReverseV:=", False)
edgeID = oEditor.GetEdgeByPosition(Array("NAME:Parameters", "BodyName:=", _
  "OuterRegion", "XPosition:=", "11.58813728906053mm", "YPosition:=", _
  "35.664619361068254mm", "ZPosition:=", "0mm"))
oModule.AssignSlave Array("NAME:Dependent1", "Edges:=", Array(edgeID), _
  "ReverseU:=", True, "Master:=", "Independent1", "SameAsMaster:=", True)
oDesign.SetDesignSettings Array("NAME:Design Settings Data", "ModelDepth:=", _
  "70mm")
Set oModule = oDesign.GetModule("AnalysisSetup")
oModule.InsertSetup "Transient", Array("NAME:Setup1", "StopTime:=", "0.008s", _
  "TimeStep:=", "4e-05s")
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.SetMinimumTimeStep "0.0004ms" 
oEditor.ShowWindow 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SlotCore", "Version:=", "12.1", "NoOfParameters:=", 19_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
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
  "Value:=", "15deg"), Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", _
  "0mm"), Array("NAME:Pair", "Name:=", "InfoCore", "Value:=", "0"))), Array(_
  "NAME:Attributes", "Name:=", "Stator", "Flags:=", "", "Color:=", _
  "(132 132 193)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "steel_1008_2DSF0.950", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/LapCoil", "Version:=", "16.0", "NoOfParameters:=", 22_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
  ), Array("NAME:Pair", "Name:=", "Slots", "Value:=", "15"), Array(_
  "NAME:Pair", "Name:=", "SlotType", "Value:=", "1"), Array("NAME:Pair", _
  "Name:=", "Hs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Hs1", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Hs2", "Value:=", "1mm"), _
  Array("NAME:Pair", "Name:=", "Bs0", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Bs1", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs2", _
  "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Rs", "Value:=", "0.5mm"), _
  Array("NAME:Pair", "Name:=", "FilletType", "Value:=", "0"), Array(_
  "NAME:Pair", "Name:=", "Layers", "Value:=", "2"), Array("NAME:Pair", _
  "Name:=", "CoilPitch", "Value:=", "1"), Array("NAME:Pair", "Name:=", _
  "EndExt", "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SpanExt", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "BendAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", "10deg"), _
  Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", "0mm"), Array(_
  "NAME:Pair", "Name:=", "InfoCoil", "Value:=", "2"))), Array(_
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
oEditor.Unite Array("NAME:Selections", "Selections:=", "Coil_0,Coil_3,Coil_6" & _
  ",Coil_9,Coil_12"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.Unite Array("NAME:Selections", "Selections:=", "Coil_1,Coil_4,Coil_7" & _
  ",Coil_10,Coil_13"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.Unite Array("NAME:Selections", "Selections:=", "Coil_2,Coil_5,Coil_8" & _
  ",Coil_11,Coil_14"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/LapCoil", "Version:=", "16.0", "NoOfParameters:=", 22_
  , "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "70mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "150mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Skew", "Value:=", "0deg"_
  ), Array("NAME:Pair", "Name:=", "Slots", "Value:=", "15"), Array(_
  "NAME:Pair", "Name:=", "SlotType", "Value:=", "1"), Array("NAME:Pair", _
  "Name:=", "Hs0", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Hs1", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Hs2", "Value:=", "1mm"), _
  Array("NAME:Pair", "Name:=", "Bs0", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Bs1", "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Bs2", _
  "Value:=", "1mm"), Array("NAME:Pair", "Name:=", "Rs", "Value:=", "0.5mm"), _
  Array("NAME:Pair", "Name:=", "FilletType", "Value:=", "0"), Array(_
  "NAME:Pair", "Name:=", "Layers", "Value:=", "2"), Array("NAME:Pair", _
  "Name:=", "CoilPitch", "Value:=", "1"), Array("NAME:Pair", "Name:=", _
  "EndExt", "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "SpanExt", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "BendAngle", "Value:=", _
  "0deg"), Array("NAME:Pair", "Name:=", "SegAngle", "Value:=", "10deg"), _
  Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", "0mm"), Array(_
  "NAME:Pair", "Name:=", "InfoCoil", "Value:=", "3"))), Array(_
  "NAME:Attributes", "Name:=", "CoilRe", "Flags:=", "", "Color:=", _
  "(250 167 14)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "copper_60C", "SolveInside:=", True) 
oEditor.Rotate Array("NAME:Selections", "Selections:=", "CoilRe"), Array(_
  "NAME:RotateParameters", "CoordinateSystemID:=", -1, "RotateAxis:=", "Z", _
  "RotateAngle:=", "-24deg")
oEditor.DuplicateAroundAxis Array("NAME:Selections", "Selections:=", "CoilRe"_
  ), Array("NAME:DuplicateAroundAxisParameters", "CoordinateSystemID:=", -1, _
  "CreateNewObjects:=", True, "WhichAxis:=", "Z", "AngleStr:=", "24deg", _
  "NumClones:=", "15"), Array("NAME:Options", "DuplicateBoundaries:=", False)
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "CoilRe"), Array(_
  "NAME:ChangedProps", Array("NAME:Name", "Value:=", "CoilRe_0"))))
oEditor.Unite Array("NAME:Selections", "Selections:=", "CoilRe_0,CoilRe_3" & _
  ",CoilRe_6,CoilRe_9,CoilRe_12"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.Unite Array("NAME:Selections", "Selections:=", "CoilRe_1,CoilRe_4" & _
  ",CoilRe_7,CoilRe_10,CoilRe_13"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.Unite Array("NAME:Selections", "Selections:=", "CoilRe_2,CoilRe_5" & _
  ",CoilRe_8,CoilRe_11,CoilRe_14"), Array("NAME:UniteParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignWindingGroup Array("NAME:PhaseA", "Type:=", "Voltage", _
  "IsSolid:=", False, "Current:=", "0A", "Voltage:=", _
  "244.949*sin(2*pi*250*time)", "Resistance:=", "272.93907ohm", _
  "Inductance:=", "4.9068225e-06H", "ParallelBranchesNum:=", "1")
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignWindingGroup Array("NAME:PhaseB", "Type:=", "Voltage", _
  "IsSolid:=", False, "Current:=", "0A", "Voltage:=", _
  "244.949*sin(2*pi*250*time-2*pi/3)", "Resistance:=", "272.93907ohm", _
  "Inductance:=", "4.9068225e-06H", "ParallelBranchesNum:=", "1")
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignWindingGroup Array("NAME:PhaseC", "Type:=", "Voltage", _
  "IsSolid:=", False, "Current:=", "0A", "Voltage:=", _
  "244.949*sin(2*pi*250*time-4*pi/3)", "Resistance:=", "272.93907ohm", _
  "Inductance:=", "4.9068225e-06H", "ParallelBranchesNum:=", "1")
oModule.AssignCoil Array("NAME:PhA_0", "Objects:=", Array("Coil_0"), _
  "Conductor number:=", 5, "PolarityType:=", "Positive", "Winding:=", _
  "PhaseA")
oModule.AssignCoil Array("NAME:PhARe_0", "Objects:=", Array("CoilRe_1"), _
  "Conductor number:=", 5, "PolarityType:=", "Negative", "Winding:=", _
  "PhaseA")
oModule.AssignCoil Array("NAME:PhB_1", "Objects:=", Array("Coil_1"), _
  "Conductor number:=", 5, "PolarityType:=", "Positive", "Winding:=", _
  "PhaseB")
oModule.AssignCoil Array("NAME:PhBRe_1", "Objects:=", Array("CoilRe_2"), _
  "Conductor number:=", 5, "PolarityType:=", "Negative", "Winding:=", _
  "PhaseB")
oModule.AssignCoil Array("NAME:PhC_2", "Objects:=", Array("Coil_2"), _
  "Conductor number:=", 5, "PolarityType:=", "Positive", "Winding:=", _
  "PhaseC")
oModule.AssignCoil Array("NAME:PhCRe_14", "Objects:=", Array("CoilRe_0"), _
  "Conductor number:=", 5, "PolarityType:=", "Negative", "Winding:=", _
  "PhaseC")
Set oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport "Stator Currents", "Transient", "XY Plot", _
  "Setup1 : Transient", Array(), Array("Time:=", Array("All")), Array(_
  "X Component:=", "Time", "Y Component:=", Array("Current(PhaseA)", _
  "Current(PhaseB)", "Current(PhaseC)")), Array()
oEditor.ShowWindow 
Set oModule = oDesign.GetModule("BoundarySetup")
oModule.SetupYConnection Array(Array("NAME:YConnection", "Windings:=", _
  "PhaseA,PhaseB,PhaseC"))
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SynRMCore", "Version:=", "12.0", "NoOfParameters:=", _
  15, "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "20mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Poles", "Value:=", "10"), _
  Array("NAME:Pair", "Name:=", "PoleType", "Value:=", "4"), Array("NAME:Pair"_
  , "Name:=", "Barriers", "Value:=", "2"), Array("NAME:Pair", "Name:=", "H", _
  "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "W", "Value:=", "2mm"), _
  Array("NAME:Pair", "Name:=", "R", "Value:=", "0.2021804002172839mm"), _
  Array("NAME:Pair", "Name:=", "R0", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Rb", "Value:=", "15mm"), Array("NAME:Pair", "Name:=", "Y0", _
  "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "B0", "Value:=", "2mm"), _
  Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", "0mm"), Array(_
  "NAME:Pair", "Name:=", "InfoCore", "Value:=", "0"))), Array(_
  "NAME:Attributes", "Name:=", "Rotor", "Flags:=", "", "Color:=", _
  "(132 132 193)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "steel_1008_2DSF1.000", "SolveInside:=", True) 
oEditor.CreateUserDefinedPart Array("NAME:UserDefinedPrimitiveParameters", _
  "DllName:=", "RMxprt/SynRMCore", "Version:=", "12.0", "NoOfParameters:=", _
  15, "Library:=", "syslib", Array("NAME:ParamVector", Array("NAME:Pair", _
  "Name:=", "DiaGap", "Value:=", "69mm"), Array("NAME:Pair", "Name:=", _
  "DiaYoke", "Value:=", "20mm"), Array("NAME:Pair", "Name:=", "Length", _
  "Value:=", "0mm"), Array("NAME:Pair", "Name:=", "Poles", "Value:=", "10"), _
  Array("NAME:Pair", "Name:=", "PoleType", "Value:=", "4"), Array("NAME:Pair"_
  , "Name:=", "Barriers", "Value:=", "2"), Array("NAME:Pair", "Name:=", "H", _
  "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "W", "Value:=", "2mm"), _
  Array("NAME:Pair", "Name:=", "R", "Value:=", "0.2021804002172839mm"), _
  Array("NAME:Pair", "Name:=", "R0", "Value:=", "1mm"), Array("NAME:Pair", _
  "Name:=", "Rb", "Value:=", "15mm"), Array("NAME:Pair", "Name:=", "Y0", _
  "Value:=", "2mm"), Array("NAME:Pair", "Name:=", "B0", "Value:=", "2mm"), _
  Array("NAME:Pair", "Name:=", "LenRegion", "Value:=", "0mm"), Array(_
  "NAME:Pair", "Name:=", "InfoCore", "Value:=", "100"))), Array(_
  "NAME:Attributes", "Name:=", "InnerRegion", "Flags:=", "", "Color:=", _
  "(0 255 255)", "Transparency:=", 0, "PartCoordinateSystem:=", "Global", _
  "MaterialName:=", "vacuum", "SolveInside:=", True) 
On Error Resume Next
Set oModule = oDesign.GetModule("MeshSetup")
oModule.AssignTrueSurfOp Array("NAME:SurfApprox_Main", "Objects:=", Array(_
  "Stator", "Rotor", "Band", "OuterRegion", "InnerRegion", "Shaft"), _
  "SurfDevChoice:=", 2, "SurfDev:=", "0.075mm", "NormalDevChoice:=", 2, _
  "NormalDev:=", "15deg", "AspectRatioChoice:=", 1)
Set oModule = oDesign.GetModule("MeshSetup")
oModule.ReassignOp "SurfApprox_Main", Array("Objects:=", Array("Stator", _
  "Rotor", "Band", "OuterRegion", "InnerRegion", "Shaft"))
On Error Goto 0
oEditor.ChangeProperty Array("NAME:AllTabs", Array(_
  "NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Band", _
  "OuterRegion", "InnerRegion"), Array("NAME:ChangedProps", Array(_
  "NAME:Transparent", "Value:=", 0.75))))
oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "Band,InnerRegion" & _
  ",Shaft,Stator,Coil_0,Coil_1,Coil_2,CoilRe_0,CoilRe_1,CoilRe_2,Rotor", _
  "Tool Parts:=", tool(0)), Array("NAME:SubtractParameters", _
  "CoordinateSystemID:=", -1, "KeepOriginals:=", False)
oEditor.FitAll 
Set oModule = oDesign.GetModule("ModelSetup")
oModule.AssignBand Array("NAME:MotionSetup1", "Move Type:=", "Rotate", _
  "Coordinate System:=", "Global", "Axis:=", "Z", "Is Positive:=", True, _
  "InitPos:=", "24deg", "HasRotateLimit:=", False, "NonCylindrical:=", _
  False, "Consider Mechanical Transient:=", True, "Angular Velocity:=", _
  "3000rpm", "Moment of Inertia:=", 0.0012175953, "Damping:=", 2.0264237e-05_
  , "Load Torque:=", "if(speed<282.743, -3.75264e-05*speed, -3/speed)", _
  "Objects:=", Array("Band"))
oModule.EditMotionSetup "MotionSetup1", Array("NAME:Data", _
  "Consider Mechanical Transient:=", False)
Set oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport "Torque", "Transient", "XY Plot", "Setup1 : Transient", _
  Array(), Array("Time:=", Array("All")), Array("X Component:=", "Time", _
  "Y Component:=", Array("Moving1.Torque")), Array()
oEditor.ShowWindow 
Set oModule = oDesign.GetModule("OutputVariable")
oModule.CreateOutputVariable "pos", "(Moving1.Position -24 * PI/180) * 5 + PI"_
  , "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "cos0", "cos(pos)", "Setup1 : Transient", _
  "Transient", Array() 
oModule.CreateOutputVariable "cos1", "cos(pos-2*PI/3)", "Setup1 : Transient", _
  "Transient", Array() 
oModule.CreateOutputVariable "cos2", "cos(pos-4*PI/3)", "Setup1 : Transient", _
  "Transient", Array() 
oModule.CreateOutputVariable "sin0", "-sin(pos)", "Setup1 : Transient", _
  "Transient", Array() 
oModule.CreateOutputVariable "sin1", "-sin(pos-2*PI/3)", "Setup1 : Transient"_
  , "Transient", Array() 
oModule.CreateOutputVariable "sin2", "-sin(pos-4*PI/3)", "Setup1 : Transient"_
  , "Transient", Array() 
oModule.CreateOutputVariable "Lad", _
  "L(PhaseA,PhaseA)*cos0 + L(PhaseA,PhaseB)*cos1 + L(PhaseA,PhaseC)*cos2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Laq", _
  "L(PhaseA,PhaseA)*sin0 + L(PhaseA,PhaseB)*sin1 + L(PhaseA,PhaseC)*sin2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Lbd", _
  "L(PhaseB,PhaseA)*cos0 + L(PhaseB,PhaseB)*cos1 + L(PhaseB,PhaseC)*cos2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Lbq", _
  "L(PhaseB,PhaseA)*sin0 + L(PhaseB,PhaseB)*sin1 + L(PhaseB,PhaseC)*sin2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Lcd", _
  "L(PhaseC,PhaseA)*cos0 + L(PhaseC,PhaseB)*cos1 + L(PhaseC,PhaseC)*cos2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Lcq", _
  "L(PhaseC,PhaseA)*sin0 + L(PhaseC,PhaseB)*sin1 + L(PhaseC,PhaseC)*sin2", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "L_d", "(Lad*cos0 + Lbd*cos1 + Lcd*cos2) * 2/3", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "L_q", "(Laq*sin0 + Lbq*sin1 + Lcq*sin2) * 2/3", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Flux_d", _
  "(FluxLinkage(PhaseA)*cos0+FluxLinkage(PhaseB)*cos1+FluxLinkage(PhaseC)*cos2)*2/3"_
  , "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Flux_q", _
  "(FluxLinkage(PhaseA)*sin0+FluxLinkage(PhaseB)*sin1+FluxLinkage(PhaseC)*sin2)*2/3"_
  , "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "I_d", _
  "(Current(PhaseA)*cos0 + Current(PhaseB)*cos1 + Current(PhaseC)*cos2)*2/3"_
  , "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "I_q", _
  "(Current(PhaseA)*sin0 + Current(PhaseB)*sin1 + Current(PhaseC)*sin2)*2/3"_
  , "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Irms", "sqrt(I_d^2+I_q^2)/sqrt(2.0)", _
  "Setup1 : Transient", "Transient", Array() 
oModule.CreateOutputVariable "Pcu", "3*Irms^2*272.939", "Setup1 : Transient", _
  "Transient", Array() 
Set oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport "L_dq", "Transient", "XY Plot", "Setup1 : Transient", _
  Array(), Array("Time:=", Array("All")), Array("X Component:=", "Time", _
  "Y Component:=", Array("L_d", "L_q")), Array()
oModule.CreateReport "Flux_dq", "Transient", "XY Plot", "Setup1 : Transient", _
  Array(), Array("Time:=", Array("All")), Array("X Component:=", "Time", _
  "Y Component:=", Array("Flux_d", "Flux_q")), Array()
oModule.CreateReport "I_dq", "Transient", "XY Plot", "Setup1 : Transient", _
  Array(), Array("Time:=", Array("All")), Array("X Component:=", "Time", _
  "Y Component:=", Array("I_d", "I_q")), Array()
oDesign.SetDesignSettings Array("NAME:Design Settings Data", _
  "ComputeTransientInductance:=", True, "ComputeIncrementalMatrix:=", False)
oEditor.ShowWindow 
Set oModule = oDesign.GetModule("AnalysisSetup")
oModule.EditSetup "Setup1", Array("NAME:Setup1", "StopTime:=", "0.04s")
if (Enable > 0) then 
oDesktop.EnableAutoSave True
end if
