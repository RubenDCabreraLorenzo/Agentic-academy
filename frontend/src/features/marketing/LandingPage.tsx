/** The public landing page (US2; FR-012, public content contract). */
import "./strings";
import { ChallengeShowcase } from "./ChallengeShowcase";
import { ClosingAction } from "./ClosingAction";
import { CompetenciesSection } from "./CompetenciesSection";
import { CurriculumSection } from "./CurriculumSection";
import { Hero } from "./Hero";
import { LabShowcase } from "./LabShowcase";
import { Methodology } from "./Methodology";
import { PrerequisitesSection } from "./PrerequisitesSection";

export default function LandingPage() {
  return (
    <div className="landing">
      <Hero />
      <Methodology />
      <CurriculumSection />
      <ChallengeShowcase />
      <LabShowcase />
      <CompetenciesSection />
      <PrerequisitesSection />
      <ClosingAction />
    </div>
  );
}
