import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorState } from "../components/states";

export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("render error", error.name, info.componentStack?.slice(0, 200));
  }

  render() {
    if (this.state.error) return <ErrorState onRetry={() => this.setState({ error: null })} />;
    return this.props.children;
  }
}
