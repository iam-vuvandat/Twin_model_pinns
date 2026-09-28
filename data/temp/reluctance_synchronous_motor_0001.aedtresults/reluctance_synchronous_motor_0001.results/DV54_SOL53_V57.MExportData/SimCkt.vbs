' ----------------------------------------------------------------------
' Script Created by RMxprt to generate Simplorer Circuit design         
' Expect 1 arg for the design name,                                     
' ----------------------------------------------------------------------

oModName = "Setup1"

Set oAnsoftApp = CreateObject("AnsoftSimplorer.SimplorerScript")
Set oArgs = AnsoftScript.arguments
Set oDesktop = oAnsoftApp.GetAppDesktop()
' ------------------------------------------------------------------------- 
' Determine the path of this vbs and resolve path to other referenced files 
' ------------------------------------------------------------------------- 
vbspath = AnsoftScript.GetScriptPath()
Set filesys = CreateObject("Scripting.FileSystemObject")
dir = filesys.GetParentFolderName(vbspath)
fileName = filesys.GetFileName(vbspath)
fileName = filesys.GetBaseName(fileName)
pathArray0 = Split(fileName, "_")
' Form the path
count = UBound(pathArray0) - 1
if (count > 0) then 
for i = 0 to count
path = path + pathArray0(i)
if (i < count) then 
path = path + "_"
end if
next
oSml1 = dir + "/" + path + ".sml"
oSml2 = dir + "/" + path + "_signals.sml"
else 
oSml1 = dir + "/" + oModName + ".sml"
oSml2 = dir + "/" + "signals.sml"
end if
Enable = oDesktop.GetAutoSaveEnabled()
oDesktop.EnableAutoSave False
Set oProject = oDesktop.GetActiveProject()
if (oArgs.Count > 1) then 
oProject.InsertDesign "Twin Builder", oArgs(1), "", ""
else 
oProject.InsertDesign "Twin Builder", "", "", ""
end if
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("SchematicEditor")
Set oDefinitionManager = oProject.GetDefinitionManager()
Set oComponentManager = oDefinitionManager.GetManager("Component")

oComponentManager.ImportModelsFromFile oSml1, Array("NAME:Options", "Mode:=", _
  1)
oComponentManager.ImportModelsFromFile oSml2, Array("NAME:Options", "Mode:=", _
  1)
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", "Setup1", _
  "Id:=", "35"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.05334, "Y:="_
  , -0.03048, "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@Setup1;35;0"), Array(_
  "NAME:ChangedProps", Array("NAME:InstanceName", "OverridingDef:=", True, _
  "Value:=", "SYNRM"))))
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "A", _
  "Id:=", 42), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04572, "Y:=", _
  -0.02794, "Degrees:=", 0, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", -0.00254, "ydelta:=", 0, "Disconnect:="_
  , False, "Rubberband:=", False)
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "B", _
  "Id:=", 49), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04572, "Y:=", _
  -0.03048, "Degrees:=", 0, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", -0.00254, "ydelta:=", 0, "Disconnect:="_
  , False, "Rubberband:=", False)
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "C", _
  "Id:=", 56), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04572, "Y:=", _
  -0.03302, "Degrees:=", 0, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", -0.00254, "ydelta:=", 0, "Disconnect:="_
  , False, "Rubberband:=", False)
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "N", _
  "Id:=", 63), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.06096, "Y:=", _
  -0.02794, "Degrees:=", 180, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", 0.00254, "ydelta:=", 0, "Disconnect:=", _
  False, "Rubberband:=", False)
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "ROT1", _
  "Id:=", 70), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.06096, "Y:=", _
  -0.03048, "Degrees:=", 180, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", 0.00254, "ydelta:=", 0, "Disconnect:=", _
  False, "Rubberband:=", False)
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "ROT2", _
  "Id:=", 77), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.06096, "Y:=", _
  -0.03302, "Degrees:=", 180, "Flip:=", False) )
oEditor.Move Array("NAME:Selections", "Selections:=", Array(ppID)), Array(_
  "NAME:MoveParameters", "xdelta:=", 0.00254, "ydelta:=", 0, "Disconnect:=", _
  False, "Rubberband:=", False)
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Physical Domains/Mechanical/Velocity-Force-Representation/Rotational_V:V_ROT"_
  , "Id:=", "84"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.09144, _
  "Y:=", -0.0254, "Degrees:=", 180, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@V_ROT;84;0"), Array("NAME:ChangedProps"_
  , Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "speed"_
  ))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@V_ROT;84;0"), Array("NAME:ChangedProps", _
  Array("NAME:VALUE", "OverridingDef:=", True, "Value:=", "3000rpm"))))
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "ROT1", _
  "Id:=", 91), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.08636, "Y:=", _
  -0.02794, "Degrees:=", 0, "Flip:=", False) )
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "ROT2", _
  "Id:=", 98), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.08636, "Y:=", _
  -0.0381, "Degrees:=", 0, "Flip:=", False) )
oEditor.CreateGround Array("NAME:GroundProps", "Id:=", "28"), Array(_
  "NAME:Attributes", "Page:=", 1, "X:=", 0.08636, "Y:=", -0.04064, _
  "Degrees:=", 0, "Flip:=", False) 
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Measurement/Electrical:AM", "Id:=", _
  "105"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04318, "Y:=", _
  0.00762, "Degrees:=", 90, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@AM;105;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "IA"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@AM;105;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Measurement/Electrical:AM", "Id:=", _
  "112"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04318, "Y:=", _
  -0.00254, "Degrees:=", 90, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@AM;112;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "IB"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@AM;112;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Measurement/Electrical:AM", "Id:=", _
  "119"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04318, "Y:=", _
  -0.0127, "Degrees:=", 90, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@AM;119;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "IC"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@AM;119;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "A", _
  "Id:=", 126), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04826, "Y:=", _
  0.01016, "Degrees:=", 180, "Flip:=", False) )
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "B", _
  "Id:=", 133), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04826, "Y:=", _
  0, "Degrees:=", 180, "Flip:=", False) )
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "C", _
  "Id:=", 140), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.04826, "Y:=", _
  -0.01016, "Degrees:=", 180, "Flip:=", False) )
ppID = oEditor.CreatePagePort( Array("NAME:PagePortProps", "Name:=", "N", _
  "Id:=", 147), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.07874, "Y:=", _
  0, "Degrees:=", 0, "Flip:=", False) )
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Measurement/Electrical:VM", "Id:=", _
  "154"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.08382, "Y:=", _
  -0.00254, "Degrees:=", 90, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@VM;154;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.CreateGround Array("NAME:GroundProps", "Id:=", "28"), Array(_
  "NAME:Attributes", "Page:=", 1, "X:=", 0.0889, "Y:=", -0.00254, "Degrees:="_
  , 0, "Flip:=", False) 
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0, -0.0381)", "(0.0254, -0.0381)")), Array("NAME:Attributes", "Page:=", 1_
  ) 
oEditor.CreateGround Array("NAME:GroundProps", "Id:=", "28"), Array(_
  "NAME:Attributes", "Page:=", 1, "X:=", 0.0127, "Y:=", -0.04064, "Degrees:="_
  , 0, "Flip:=", False) 
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0, -0.0381)", "(0, -0.03556)")), Array("NAME:Attributes", "Page:=", 1) 
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Circuit/Sources:E", "Id:=", "161"), _
  Array("NAME:Attributes", "Page:=", 1, "X:=", -0.00254, "Y:=", -0.03048, _
  "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@E;161;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "VA"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", _
  Array("NAME:Type", "OverridingDef:=", True, "Value:=", "ESINE"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", Array(_
  "NAME:AMPL", "OverridingDef:=", True, "Value:=", "244.949V"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", Array(_
  "NAME:FREQ", "OverridingDef:=", True, "Value:=", "250Hz"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", Array(_
  "NAME:TPERIO", "OverridingDef:=", True, "Value:=", "0.004s"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;161;0"), Array("NAME:ChangedProps", Array(_
  "NAME:PHASE", "OverridingDef:=", True, "Value:=", "0deg"))))
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0, -0.0254)", "(0, 0.01016)", "(0.0381, 0.01016)")), Array(_
  "NAME:Attributes", "Page:=", 1) 
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0.0127, -0.0381)", "(0.0127, -0.03556)")), Array("NAME:Attributes", _
  "Page:=", 1) 
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Circuit/Sources:E", "Id:=", "168"), _
  Array("NAME:Attributes", "Page:=", 1, "X:=", 0.01016, "Y:=", -0.03048, _
  "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@E;168;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "VB"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", _
  Array("NAME:Type", "OverridingDef:=", True, "Value:=", "ESINE"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", Array(_
  "NAME:AMPL", "OverridingDef:=", True, "Value:=", "244.949V"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", Array(_
  "NAME:FREQ", "OverridingDef:=", True, "Value:=", "250Hz"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", Array(_
  "NAME:TPERIO", "OverridingDef:=", True, "Value:=", "0.004s"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;168;0"), Array("NAME:ChangedProps", Array(_
  "NAME:PHASE", "OverridingDef:=", True, "Value:=", "240deg"))))
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0.0127, -0.0254)", "(0.0127, 0)", "(0.0381, 0)")), Array(_
  "NAME:Attributes", "Page:=", 1) 
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0.0254, -0.0381)", "(0.0254, -0.03556)")), Array("NAME:Attributes", _
  "Page:=", 1) 
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", _
  "Simplorer Elements/Basic Elements/Circuit/Sources:E", "Id:=", "175"), _
  Array("NAME:Attributes", "Page:=", 1, "X:=", 0.02286, "Y:=", -0.03048, _
  "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PropDisplayPropTab", _
  Array("NAME:PropServers", "CompInst@E;175;0"), Array("NAME:NewProps", _
  Array("NAME:InstanceName", "Format:=", "Value", "Location:=", "Right"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", _
  Array("NAME:InstanceName", "OverridingDef:=", True, "Value:=", "VC"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", _
  Array("NAME:Type", "OverridingDef:=", True, "Value:=", "ESINE"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", Array(_
  "NAME:AMPL", "OverridingDef:=", True, "Value:=", "244.949V"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", Array(_
  "NAME:FREQ", "OverridingDef:=", True, "Value:=", "250Hz"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", Array(_
  "NAME:TPERIO", "OverridingDef:=", True, "Value:=", "0.004s"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Quantities", Array(_
  "NAME:PropServers", "CompInst@E;175;0"), Array("NAME:ChangedProps", Array(_
  "NAME:PHASE", "OverridingDef:=", True, "Value:=", "120deg"))))
oEditor.CreateWire Array("NAME:WireData", "Id:=", "1", "Points:=", Array(_
  "(0.0254, -0.0254)", "(0.0254, -0.01016)", "(0.0381, -0.01016)")), Array(_
  "NAME:Attributes", "Page:=", 1) 
Set oModule = oDesign.GetModule("SimSetup")
oModule.EditTransient "TR", Array("NAME:SimSetup", "OptionName:=", _
  "(Default Options)", "AnalysisEnabled:=", 1, "Name:=", "TR", _
  "TransientData:=", Array("20ms", "0.4us", "4us", false, ""), _
  "EnableContSolve:=", False)
Set oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport "Load Torque", "Standard", "Rectangular Plot", "TR", _
  Array("NAME:Context", "SimValueContext:=", _
  Array(1, 0, 2, 0, False, False, -1, 1, 0, 1, 1, "", 0, 0)), Array("Time:="_
  , Array("All")), Array("X Component:=", "Time", "Y Component:=", Array(_
  "speed.TORQUE")), Array()
oModule.CreateReport "Current", "Standard", "Rectangular Plot", "TR", Array(_
  "NAME:Context", "SimValueContext:=", _
  Array(1, 0, 2, 0, False, False, -1, 1, 0, 1, 1, "", 0, 0)), Array("Time:="_
  , Array("All")), Array("X Component:=", "Time", "Y Component:=", Array(_
  "IA.I", "IB.I", "IC.I")), Array()
sName = oDesign.GetName()
arr = Split(sName, ";")
oProject.SetActiveDesign arr(1)
oEditor.ZoomToFit 
if (oArgs.Count > 0) then 
oProject.SaveAs oArgs(0), True
end if
if (Enable > 0) then 
oDesktop.EnableAutoSave True
end if
