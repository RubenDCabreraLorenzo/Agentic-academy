/** Owner-supplied legal text. Without its file, the route is not found (FR-022a). */
import { useQuery } from "@tanstack/react-query";
import { NotFound } from "../../app/NotFound";
import { Markdown } from "../../components/content/Markdown";
import { ErrorState, Loading } from "../../components/states";
import { legal, type LegalLoader } from "./availability";

function LegalDocument({ id, load }: { id: string; load: LegalLoader }) {
  const q = useQuery({ queryKey: ["legal", id], queryFn: load, staleTime: Infinity });
  if (q.isLoading) return <Loading />;
  if (q.isError || q.data === undefined) return <ErrorState onRetry={() => q.refetch()} />;
  return (
    <article className="reading stack">
      <Markdown source={q.data} deprecations={{}} />
    </article>
  );
}

export function PrivacyPage() {
  return legal.privacy ? <LegalDocument id="privacy" load={legal.privacy} /> : <NotFound />;
}

export function TermsPage() {
  return legal.terms ? <LegalDocument id="terms" load={legal.terms} /> : <NotFound />;
}
