import { useEffect, useRef } from "react";
import { ContentMeta } from "../../components/content/Callouts";
import { Markdown } from "../../components/content/Markdown";
import type { ModuleDetail } from "../catalog/types";

type Lesson = ModuleDetail["lessons"][number];

/** One lesson; reports when it becomes visible so the learner's position can be saved. */
export function LessonView({
  lesson,
  deprecations,
  onVisible,
}: {
  lesson: Lesson;
  deprecations: ModuleDetail["deprecations"];
  onVisible: (lessonId: string) => void;
}) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    let reported = false;
    const io = new IntersectionObserver(
      (entries) => {
        if (!reported && entries.some((e) => e.isIntersecting)) {
          reported = true;
          onVisible(lesson.id);
        }
      },
      { threshold: 0.25 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [lesson.id, onVisible]);

  return (
    <section ref={ref} aria-labelledby={`lesson-${lesson.id}`} className="reading stack" id={`lesson-${lesson.id}`}>
      <h2 id={`lesson-${lesson.id}`}>{lesson.title}</h2>
      <ContentMeta version={lesson.version} lastReviewed={lesson.last_reviewed} deprecation={lesson.deprecation} />
      <Markdown source={lesson.body_markdown} deprecations={deprecations} />
    </section>
  );
}
