import Cerp
open Cerp
-- Axiom audit of every core theorem (expected: at most propext, Quot.sound, Classical.choice)
#print axioms decideEquiv_correct
#print axioms decideTask_correct
#print axioms eval_congr
#print axioms allEnvs_complete
#print axioms propagate_sound
#print axioms rup_sound
#print axioms checkAll_sound
#print axioms unsat_of_certificate
#print axioms checkLrat_sound
#print axioms tseitinMiter_lrat_unsat_implies_equiv
#print axioms evalTNetFrom_congr
#print axioms decideTNetEquivExpr_correct
#print axioms eval_pbToExpr
#print axioms tseitinTNetMiter_lrat_unsat_implies_equiv
#print axioms tseitinTNetMiterPB_lrat_unsat_implies_equiv
