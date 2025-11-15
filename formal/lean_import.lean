import Std.Data.HashMap
import Lean.Data.Json

open Lean Std

structure WindowWitness where
  residue : Nat
  j : Nat
  K : Nat
  pattern : List Nat
  A : Rat
  B : Rat
  N0 : Rat
deriving Repr

structure FunnelWitness where
  residue : Nat
  length : Nat
deriving Repr

def summaryPath : System.FilePath := "artifacts/summary.json"
def windowsPath : System.FilePath := "artifacts/windows.csv"
def funnelsPath : System.FilePath := "artifacts/funnels.csv"

def parseFraction (s : String) : Except String Rat :=
  match s.splitOn "/" with
  | [num] => return Rat.ofInt num.toInt!
  | [num, denom] =>
      if denom.toInt! = 0 then
        throw <| "zero denominator in " ++ s
      else
        return Rational.mk num.toInt! denom.toInt!
  | _ => throw <| "invalid fraction: " ++ s

/-
  Placeholder for CSV parsing. In a full formalization this function would:
  * load the CSV
  * ensure hashes match `summary.json`
  * convert each row into a `WindowWitness`
  * prove the congruence relations
-/
def loadWindows : IO (Array WindowWitness) := do
  if ← windowsPath.pathExists then
    pure #[]
  else
    throw <| IO.userError s!"Missing windows csv at {windowsPath}"

def loadFunnels : IO (Array FunnelWitness) := do
  if ← funnelsPath.pathExists then
    pure #[]
  else
    throw <| IO.userError s!"Missing funnels csv at {funnelsPath}"

/-
  High-level statement sketch
-/
theorem collatz_of_certificate
    (windows : Array WindowWitness)
    (funnels : Array FunnelWitness)
    (certified : True) :
    True := by
  -- replace with the real argument once the data import is formalized
  trivial
