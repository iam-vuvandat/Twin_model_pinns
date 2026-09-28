' -------------------------------------------------------------------------
' Script Created by RMxprt to generate external circuit                    
' Expect 2 args, first the design name,                                    
'                second the path to export netlist                         
' -------------------------------------------------------------------------

Set oAnsoftApp = CreateObject("AnsoftMaxCir.MaxCirScript")
Set oArgs = AnsoftScript.arguments
Set oDesktop = oAnsoftApp.GetAppDesktop()
oDesktop.RestoreWindow 
Enable = oDesktop.GetAutoSaveEnabled()
oDesktop.EnableAutoSave False
Set oProject = oDesktop.GetActiveProject()
if (oArgs.Count > 0) then 
oProject.InsertDesign "Maxwell Circuit", oArgs(0), "", ""
else 
oProject.InsertDesign "Maxwell Circuit", "", "", ""
end if
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("SchematicEditor")
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array(_
  "NAME:Kle", "PropType:=", "VariableProp", "UserDef:=", True, "Value:=", "1"_
  ))))
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", "ECE3_Model", _
  "Id:=", "14"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0, "Y:=", 0, _
  "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECE3_Model;14;0"), Array(_
  "NAME:ChangedProps", Array("NAME:Windings", "OverridingDef:=", True, _
  "Value:=", "PhaseA, PhaseB, PhaseC"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECE3_Model;14;0"), Array(_
  "NAME:ChangedProps", Array("NAME:CurrentSweeps", "OverridingDef:=", True, _
  "Value:=", "(5A, 2)"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECE3_Model;14;0"), Array(_
  "NAME:ChangedProps", Array("NAME:Res", "OverridingDef:=", True, "Value:=", _
  "272.93907ohm"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECE3_Model;14;0"), Array(_
  "NAME:ChangedProps", Array("NAME:IndE", "OverridingDef:=", True, "Value:="_
  , "4.9068225e-06H*Kle"))))
oEditor.CreateComponent Array("NAME:ComponentProps", "Name:=", "ECER_Model", _
  "Id:=", "21"), Array("NAME:Attributes", "Page:=", 1, "X:=", 0.0127, "Y:=", _
  0, "Degrees:=", 0, "Flip:=", False) 
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:RotAngMax", "OverridingDef:=", True, _
  "Value:=", "24"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:RotAngIntervals", "OverridingDef:=", _
  True, "Value:=", "0"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:SkewAng", "OverridingDef:=", True, _
  "Value:=", "0deg"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:Poles", "OverridingDef:=", True, "Value:="_
  , "10"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:Slots", "OverridingDef:=", True, "Value:="_
  , "0"))))
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:PassedParameterTab", _
  Array("NAME:PropServers", "CompInst@ECER_Model;21;0"), Array(_
  "NAME:ChangedProps", Array("NAME:Output", "OverridingDef:=", True, _
  "Value:=", "2"))))
oEditor.CreateGround Array("NAME:GroundProps", "Id:=", "7"), Array(_
  "NAME:Attributes", "Page:=", 1, "X:=", 0.0254, "Y:=", 0, "Degrees:=", 0, _
  "Flip:=", False) 
if (oArgs.Count > 0) then 
oProject.SetActiveDesign oArgs(0)
end if
oEditor.ZoomToFit 
if (oArgs.Count > 1) then 
oDesign.ExportNetList "", oArgs(1)
end if
if (Enable > 0) then 
oDesktop.EnableAutoSave True
end if
