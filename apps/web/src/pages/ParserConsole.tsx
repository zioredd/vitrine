import { useState } from "react";
import { apiPost } from "../api/client";
import { ErrorBanner, JsonPanel, PageShell } from "../components/PageShell";
import { API } from "../constants/api";
import { useMutation } from "../hooks/useApi";

type ParserStep = "tokenize" | "parse" | "compile";

const ENDPOINTS: Record<ParserStep, string> = {
  tokenize: API.PARSER_TOKENIZE,
  parse: API.PARSER_PARSE,
  compile: API.PARSER_COMPILE,
};

export function ParserConsole() {
  const [expression, setExpression] = useState("genre:jazz AND bpm:120");
  const [step, setStep] = useState<ParserStep>("tokenize");

  const parser = useMutation((s: ParserStep) =>
    apiPost<unknown>(ENDPOINTS[s], { expression }),
  );

  return (
    <PageShell
      title="Parser Console"
      subtitle="Tokenize, parse, and compile filter query expressions for exhibition search."
    >
      <div className="card">
        <div className="field">
          <label htmlFor="expression">Filter expression</label>
          <input
            id="expression"
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            placeholder="genre:jazz AND bpm:120"
          />
        </div>
        <div className="tabs">
          {(["tokenize", "parse", "compile"] as ParserStep[]).map((s) => (
            <button
              key={s}
              type="button"
              className={step === s ? "tab active" : "tab"}
              onClick={() => setStep(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div className="actions">
          <button
            type="button"
            className="primary"
            disabled={parser.loading}
            onClick={() => parser.mutate(step)}
          >
            {parser.loading ? "Processing…" : `Run ${step}`}
          </button>
        </div>
        {parser.error ? <ErrorBanner message={parser.error} /> : null}
        {parser.data ? <JsonPanel title={`${step} output`} data={parser.data} /> : null}
      </div>
    </PageShell>
  );
}
