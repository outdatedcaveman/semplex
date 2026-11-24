$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host '== Lake build =='
lake build Cerp Distinction SmallFibration ModuleDescent SynesismConservation HigherGaugeCohomology Theory Bounds Closure Inference CausalClosure ResponseQuotient ObservableCongruence ResourceRelativeProbes BeliefStateHankel CausalRealization CausalAnchorAdequacy StochasticInterventionGrounding StatisticalCausalAnchorAdequacy GroundingAdequacy GroundingAdequacyExample OperationalGroundingAdequacy GroundedRelativeDensity GroundedRelativeDensityExample GroundedModuliFiber GroundedModuliFiberExample GroundedSemiosisTransport GroundedSemiosisTransportExample OperationalInstitutionBridge GroundedSemiosisCoarseGraining ContextualDescentObstruction CrossTheoryConservativity StochasticCausalCovariance CausalCovarianceGroupoidBridge ObstructionExactSequence ContextualRingDescent AuditGroundedSemiosisTransport AuditGroundingAdequacy AuditOperationalGroundingAdequacy AuditOperationalGroundingSymmetry AuditGroundedRelativeDensity AuditGroundedModuliFiber AuditCausalRealization AuditContextualDescentObstruction AuditCrossTheoryConservativity AuditStochasticCausalCovariance AuditCausalCovarianceGroupoidBridge AuditObstructionExactSequence AuditContextualRingDescent Audit AuditTheory AuditBounds AuditClosure AuditInference AuditDistinction AuditFibration AuditModuleDescent AuditSynesismConservation AuditHigherGaugeCohomology AuditSemanticGrounding
if ($LASTEXITCODE -ne 0) { throw "lake build failed: $LASTEXITCODE" }

$auditFiles = @(
  'Audit.lean',
  'AuditTheory.lean',
  'AuditBounds.lean',
  'AuditClosure.lean',
  'AuditInference.lean',
  'AuditDistinction.lean',
  'AuditFibration.lean',
  'AuditModuleDescent.lean',
  'AuditSynesismConservation.lean',
  'AuditHigherGaugeCohomology.lean',
  'AuditSemanticGrounding.lean',
  'AuditCausalRealization.lean',
  'AuditCausalAnchorAdequacy.lean',
  'AuditStatisticalCausalAnchorAdequacy.lean',
  'AuditGroundingAdequacy.lean',
  'AuditOperationalGroundingAdequacy.lean',
  'AuditOperationalGroundingSymmetry.lean',
  'AuditGroundedRelativeDensity.lean',
  'AuditGroundedModuliFiber.lean',
  'AuditGroundedSemiosisTransport.lean',
  'AuditContextualDescentObstruction.lean',
  'AuditCrossTheoryConservativity.lean',
  'AuditStochasticCausalCovariance.lean',
  'AuditCausalCovarianceGroupoidBridge.lean',
  'AuditObstructionExactSequence.lean',
  'AuditContextualRingDescent.lean'
)

foreach ($file in $auditFiles) {
  Write-Host "== Axiom audit: $file =="
  lake env lean $file
  if ($LASTEXITCODE -ne 0) { throw "Axiom audit failed: $file (exit $LASTEXITCODE)" }
}

Write-Host 'ALL_LEAN_BUILDS_AND_AUDITS_PASS'
