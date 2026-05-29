import type { Message } from "@langchain/langgraph-sdk";
import {
  FileIcon,
  Loader2Icon,
  StarIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
} from "lucide-react";
import {
  memo,
  useCallback,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
  type ImgHTMLAttributes,
} from "react";
import rehypeKatex from "rehype-katex";

import { Loader } from "@/components/ai-elements/loader";
import {
  Message as AIElementMessage,
  MessageContent as AIElementMessageContent,
  MessageResponse as AIElementMessageResponse,
  MessageToolbar,
} from "@/components/ai-elements/message";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import { Task, TaskTrigger } from "@/components/ai-elements/task";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  deleteFeedback,
  upsertFeedback,
  type FeedbackData,
} from "@/core/api/feedback";
import { resolveArtifactURL } from "@/core/artifacts/utils";
import { useI18n } from "@/core/i18n/hooks";
import {
  extractContentFromMessage,
  extractReasoningContentFromMessage,
  parseUploadedFiles,
  stripUploadedFilesTag,
  type FileInMessage,
} from "@/core/messages/utils";
import { useRehypeSplitWordsIntoSpans } from "@/core/rehype";
import { humanMessagePlugins } from "@/core/streamdown";
import { cn } from "@/lib/utils";

import { CopyButton } from "../copy-button";

import { MarkdownContent } from "./markdown-content";

/**
 * Roleplay evaluation data structure
 */
export interface RoleplayEvaluation {
  session_id?: string;
  customer_message?: string | null;
  evaluation?: {
    round_score?: number;
    total_score?: number;
    round_scores?: number[];
  };
  is_complete?: boolean;
  round?: number;
  total_score?: number;
  dimension_scores?: Record<string, number>;
  dimension_feedbacks?: Record<string, string>;  // 新增：各维度详细反馈
  strengths?: string[];
  improvements?: string[];
  summary?: string;
}

/**
 * Parse roleplay evaluation from Markdown format (e.g., "**本轮得分：35/100**")
 */
function parseRoleplayEvaluationFromMarkdown(content: string): RoleplayEvaluation | null {
  // Pattern to match round score: **本轮得分：XX/100**
  const roundScoreMatch = content.match(/\*\*本轮得分[：:]\s*(\d+)\/100\*\*/);
  // Pattern to match cumulative score: **累计得分：XX/100**
  const totalScoreMatch = content.match(/\*\*累计得分[：:]\s*(\d+)\/100\*\*/);
  // Pattern to match round number: **第X轮 / 共Y轮** or **第X轮 / 共Y轮（最后一轮）**
  // Use global search with multiline to find the FIRST occurrence
  const roundMatch = content.match(/\*\*第(\d+)轮\s*\/\s*共(\d+)轮/);
  // Pattern to check if it's the final round
  const isFinalMatch = content.match(/\*\*第\d+轮\s*\/\s*共\d+轮(?:（最后一轮）|\s*\(最后一轮\))/);
  // Pattern to match feedback text: **反馈：** followed by text (may span multiple lines)
  const feedbackMatch = content.match(/\*\*反馈[：:]\s*([\s\S]*?)(?=\n\n|\n---|\n\*\*|$)/);

  if (roundScoreMatch) {
    const roundScore = parseInt(roundScoreMatch[1]!, 10);
    const totalScore = totalScoreMatch ? parseInt(totalScoreMatch[1]!, 10) : roundScore;
    const currentRound = roundMatch ? parseInt(roundMatch[1]!, 10) : undefined;
    const totalRounds = roundMatch ? parseInt(roundMatch[2]!, 10) : undefined;
    // is_complete is true only if explicitly marked as "最后一轮" or currentRound matches totalRounds
    const isComplete = !!isFinalMatch || (totalRounds !== undefined && currentRound !== undefined && currentRound === totalRounds);
    const summary = feedbackMatch && feedbackMatch[1] ? feedbackMatch[1].trim() : undefined;

    return {
      round: currentRound,
      total_score: totalScore,
      evaluation: {
        round_score: roundScore,
        total_score: totalScore,
      },
      is_complete: isComplete,
      summary,
    };
  }

  return null;
}

/**
 * Parse roleplay evaluation JSON from message content (fallback for backward compatibility)
 */
export function parseRoleplayEvaluationFromContent(content: string): RoleplayEvaluation | null {
  // First try Markdown format (current backend format)
  const markdownParsed = parseRoleplayEvaluationFromMarkdown(content);
  if (markdownParsed) {
    return markdownParsed;
  }

  try {
    // Try to find JSON in the content
    const jsonMatch = content.match(/```json\n*([\s\S]*?)```/) || 
                      content.match(/```\n*([\s\S]*?)```/) ||
                      content.match(/(\{[\s\S]*\})/);
    
    if (jsonMatch && jsonMatch[1]) {
      const data = JSON.parse(jsonMatch[1].trim());
      if (data.evaluation || data.is_complete !== undefined || data.round) {
        return data as RoleplayEvaluation;
      }
    }
    
    // Try parsing the entire content as JSON
    const parsed = JSON.parse(content);
    if (parsed.evaluation || parsed.is_complete !== undefined || parsed.round) {
      return parsed as RoleplayEvaluation;
    }
  } catch {
    // Not valid JSON, ignore
  }
  return null;
}

/**
 * Roleplay Score Button Component - Icon button that opens a dialog with detailed scores
 */
function RoleplayScoreButton({
  evaluation,
}: {
  evaluation: RoleplayEvaluation;
}) {
  const hasDetailedScore = evaluation.dimension_scores || 
                           evaluation.dimension_feedbacks ||
                           evaluation.strengths || 
                           evaluation.improvements;
  
  const roundScore = evaluation.evaluation?.round_score ?? evaluation.total_score;
  const totalScore = evaluation.evaluation?.total_score;
  const roundScores = evaluation.evaluation?.round_scores;
  const round = evaluation.round;
  const isComplete = evaluation.is_complete;

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-1 rounded-md px-2 py-1 text-xs hover:bg-accent/50 transition-colors"
          title={isComplete ? "查看对练评估报告" : `第${round}轮评分`}
        >
          <StarIcon className={cn("size-3.5", isComplete ? "text-yellow-500 fill-yellow-500" : "text-muted-foreground")} />
          {roundScore !== undefined && (
            <span className={cn(
              "font-medium",
              isComplete ? "text-yellow-600" : "text-muted-foreground"
            )}>
              {roundScore}
            </span>
          )}
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <StarIcon className={cn("size-5", isComplete ? "text-yellow-500 fill-yellow-500" : "text-muted-foreground")} />
            {isComplete ? "对练评估报告" : `第${round}轮评分`}
            {roundScore !== undefined && (
              <span className="ml-auto text-2xl font-bold text-primary">
                {roundScore}
              </span>
            )}
            {totalScore !== undefined && roundScores && (
              <span className="text-sm text-muted-foreground ml-2">
                (总分: {totalScore})
              </span>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {/* Round Scores Progress */}
          {roundScores && roundScores.length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">各轮得分</div>
              <div className="flex gap-1">
                {roundScores.map((score, index) => (
                  <div
                    key={index}
                    className="flex-1 rounded bg-secondary px-2 py-1 text-center text-sm font-medium"
                  >
                    {score}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dimension Scores */}
          {evaluation.dimension_scores && Object.keys(evaluation.dimension_scores).length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">维度评分</div>
              <div className="space-y-2">
                {Object.entries(evaluation.dimension_scores).map(([dimension, score]) => (
                  <div key={dimension} className="flex items-center justify-between">
                    <span className="text-sm">{dimension}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 rounded-full bg-secondary overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{score}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dimension Feedbacks */}
          {evaluation.dimension_feedbacks && Object.keys(evaluation.dimension_feedbacks).length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">维度详细反馈</div>
              <div className="space-y-3">
                {Object.entries(evaluation.dimension_feedbacks).map(([dimension, feedback]) => (
                  <div key={dimension} className="rounded bg-secondary/30 p-3">
                    <div className="text-sm font-medium text-foreground mb-1">{dimension}</div>
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap">{feedback}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strengths */}
          {evaluation.strengths && evaluation.strengths.length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">优点</div>
              <ul className="list-disc list-inside text-sm space-y-1">
                {evaluation.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Improvements */}
          {evaluation.improvements && evaluation.improvements.length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">改进建议</div>
              <ul className="list-disc list-inside text-sm space-y-1">
                {evaluation.improvements.map((improvement, index) => (
                  <li key={index}>{improvement}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Summary */}
          {evaluation.summary && (
            <div className="rounded bg-secondary/50 p-3 text-sm">
              {evaluation.summary}
            </div>
          )}

          {/* No detailed info fallback */}
          {!hasDetailedScore && !evaluation.summary && (
            <div className="text-sm text-muted-foreground text-center py-4">
              暂无详细评分信息
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function FeedbackButtons({
  threadId,
  runId,
  initialFeedback,
}: {
  threadId: string;
  runId: string;
  initialFeedback: FeedbackData | null;
}) {
  const [feedback, setFeedback] = useState<FeedbackData | null>(
    initialFeedback,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = useCallback(
    async (rating: number) => {
      if (isSubmitting) return;
      setIsSubmitting(true);
      try {
        if (feedback?.rating === rating) {
          await deleteFeedback(threadId, runId);
          setFeedback(null);
        } else {
          const result = await upsertFeedback(threadId, runId, rating);
          setFeedback(result);
        }
      } catch {
        // Revert on error — feedback state unchanged on catch
      } finally {
        setIsSubmitting(false);
      }
    },
    [threadId, runId, feedback, isSubmitting],
  );

  return (
    <div className="flex gap-1">
      <button
        type="button"
        className={cn(
          "text-muted-foreground hover:text-foreground rounded-md p-1 transition-colors",
          feedback?.rating === 1 && "text-foreground",
        )}
        onClick={() => handleClick(1)}
        disabled={isSubmitting}
      >
        <ThumbsUpIcon
          className={cn("size-4", feedback?.rating === 1 && "fill-current")}
        />
      </button>
      <button
        type="button"
        className={cn(
          "text-muted-foreground hover:text-foreground rounded-md p-1 transition-colors",
          feedback?.rating === -1 && "text-foreground",
        )}
        onClick={() => handleClick(-1)}
        disabled={isSubmitting}
      >
        <ThumbsDownIcon
          className={cn("size-4", feedback?.rating === -1 && "fill-current")}
        />
      </button>
    </div>
  );
}

export function MessageListItem({
  className,
  message,
  isLoading,
  feedback,
  runId,
  threadId,
  showCopyButton = true,
  roleplayEvaluation: externalEvaluation,
}: {
  className?: string;
  message: Message;
  isLoading?: boolean;
  threadId: string;
  feedback?: FeedbackData | null;
  runId?: string;
  showCopyButton?: boolean;
  roleplayEvaluation?: RoleplayEvaluation | null;
}) {
  const isHuman = message.type === "human";
  
  // Use external evaluation (from parent) for human messages, extract from AI message content for backward compatibility
  const roleplayEvaluation = useMemo(() => {
    if (isHuman) {
      return externalEvaluation ?? null;
    }
    
    // For AI messages, check additional_kwargs first (from backend middleware)
    const additional_kwargs = (message as { additional_kwargs?: { evaluation?: RoleplayEvaluation } }).additional_kwargs;
    if (additional_kwargs?.evaluation) {
      return additional_kwargs.evaluation;
    }
    
    // Fall back to parsing from content
    const rawContent = extractContentFromMessage(message);
    return parseRoleplayEvaluationFromContent(rawContent ?? "");
  }, [isHuman, message, externalEvaluation]);
  
  return (
    <AIElementMessage
      className={cn("group/conversation-message relative w-full", className)}
      from={isHuman ? "user" : "assistant"}
    >
      <MessageContent
        className={isHuman ? "w-fit" : "w-full"}
        message={message}
        isLoading={isLoading}
        threadId={threadId}
        roleplayEvaluation={roleplayEvaluation}
      />
      {!isLoading && (showCopyButton || (isHuman && roleplayEvaluation)) && (
        <MessageToolbar
          className={cn(
            isHuman
              ? "absolute right-0 -bottom-9 left-0 justify-end"
              : "absolute right-0 bottom-0 left-0",
            "z-20",
            isHuman && roleplayEvaluation ? "opacity-100" : "opacity-0 transition-opacity delay-200 duration-300 group-hover/conversation-message:opacity-100",
          )}
        >
          <div className="pointer-events-auto flex gap-1">
            {isHuman && roleplayEvaluation && (
              <RoleplayScoreButton evaluation={roleplayEvaluation} />
            )}
            {showCopyButton && (
              <CopyButton
                clipboardData={
                  extractContentFromMessage(message) ??
                  extractReasoningContentFromMessage(message) ??
                  ""
                }
              />
            )}
            {feedback !== undefined && runId && threadId && (
              <FeedbackButtons
                threadId={threadId}
                runId={runId}
                initialFeedback={feedback}
              />
            )}
          </div>
        </MessageToolbar>
      )}
    </AIElementMessage>
  );
}

/**
 * Custom image component that handles artifact URLs
 */
function MessageImage({
  src,
  alt,
  threadId,
  maxWidth = "90%",
  ...props
}: React.ImgHTMLAttributes<HTMLImageElement> & {
  threadId: string;
  maxWidth?: string;
}) {
  if (!src) return null;

  const imgClassName = cn("overflow-hidden rounded-lg", `max-w-[${maxWidth}]`);

  if (typeof src !== "string") {
    return <img className={imgClassName} src={src} alt={alt} {...props} />;
  }

  const url = src.startsWith("/mnt/") ? resolveArtifactURL(src, threadId) : src;

  return (
    <a href={url} target="_blank" rel="noopener noreferrer">
      <img className={imgClassName} src={url} alt={alt} {...props} />
    </a>
  );
}

function MessageContent_({
  className,
  message,
  isLoading = false,
  threadId,
  roleplayEvaluation,
}: {
  className?: string;
  message: Message;
  isLoading?: boolean;
  threadId: string;
  roleplayEvaluation?: RoleplayEvaluation | null;
}) {
  const rehypePlugins = useRehypeSplitWordsIntoSpans(isLoading);
  const isHuman = message.type === "human";
  const components = useMemo(
    () => ({
      img: (props: ImgHTMLAttributes<HTMLImageElement>) => (
        <MessageImage {...props} threadId={threadId} maxWidth="90%" />
      ),
      a: ({ href, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) => {
        if (href?.startsWith("/mnt/")) {
          const url = resolveArtifactURL(href, threadId);
          return (
            <a
              {...props}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
            />
          );
        }
        return <a {...props} href={href} />;
      },
    }),
    [threadId],
  );

  const rawContent = extractContentFromMessage(message);
  const reasoningContent = extractReasoningContentFromMessage(message);

  const files = useMemo(() => {
    const files = message.additional_kwargs?.files;
    if (!Array.isArray(files) || files.length === 0) {
      if (rawContent.includes("<uploaded_files>")) {
        // If the content contains the <uploaded_files> tag, we return the parsed files from the content for backward compatibility.
        return parseUploadedFiles(rawContent);
      }
      return null;
    }
    return files as FileInMessage[];
  }, [message.additional_kwargs?.files, rawContent]);

  const contentToDisplay = useMemo(() => {
    if (isHuman) {
      return rawContent ? stripUploadedFilesTag(rawContent) : "";
    }
    return rawContent ?? "";
  }, [rawContent, isHuman]);

  const filesList =
    files && files.length > 0 ? (
      <RichFilesList files={files} threadId={threadId} />
    ) : null;

  // Uploading state: mock AI message shown while files upload
  if (message.additional_kwargs?.element === "task") {
    return (
      <AIElementMessageContent className={className}>
        <Task defaultOpen={false}>
          <TaskTrigger title="">
            <div className="text-muted-foreground flex w-full cursor-default items-center gap-2 text-sm select-none">
              <Loader className="size-4" />
              <span>{contentToDisplay}</span>
            </div>
          </TaskTrigger>
        </Task>
      </AIElementMessageContent>
    );
  }

  // Reasoning-only AI message (no main response content yet)
  if (!isHuman && reasoningContent && !rawContent) {
    return (
      <AIElementMessageContent className={className}>
        <Reasoning isStreaming={isLoading}>
          <ReasoningTrigger />
          <ReasoningContent>{reasoningContent}</ReasoningContent>
        </Reasoning>
      </AIElementMessageContent>
    );
  }

  if (isHuman) {
    const messageResponse = contentToDisplay ? (
      <AIElementMessageResponse
        remarkPlugins={humanMessagePlugins.remarkPlugins}
        rehypePlugins={humanMessagePlugins.rehypePlugins}
        components={components}
        parseIncompleteMarkdown={false}
      >
        {contentToDisplay}
      </AIElementMessageResponse>
    ) : null;
    return (
      <div className={cn("ml-auto flex flex-col gap-2", className)}>
        {filesList}
        {messageResponse && (
          <AIElementMessageContent className="w-fit">
            {messageResponse}
          </AIElementMessageContent>
        )}
      </div>
    );
  }

  // For roleplay evaluation, strip the evaluation section from display content
  const displayContent = useMemo(() => {
    if (roleplayEvaluation && rawContent) {
      // Remove evaluation blocks (e.g., **本轮得分：35/100** section)
      // The evaluation section is usually at the end or followed by ---
      // We want to keep the customer question part
      
      // First, try to find and remove evaluation block (everything from **本轮得分 onwards)
      // Keep everything before it (which should be the customer question)
      const evalStartRegex = /(^|\n)(?=\*\*本轮得分)/;
      const evalStartIndex = rawContent.search(evalStartRegex);
      if (evalStartIndex !== -1) {
        const prefix = rawContent.substring(0, evalStartIndex);
        return prefix.trim();
      }
      
      // If no **本轮得分 found, try --- separator
      const parts = rawContent.split(/---\s*\n/);
      if (parts.length >= 2) {
        // parts[0] = evaluation section, parts[1+] = next round's content
        return parts.slice(1).join("---\n").trim();
      }
      
      // If no --- separator, try to remove just the evaluation block
      return rawContent
        .replace(/\*\*第\d+轮评估[：:]\*\*[\s\S]*?(\*\*反馈[：:][\s\S]*?)?(?=\n\n|\n---|$)/g, "")
        .replace(/```json\n*[\s\S]*?```/g, "")
        .replace(/```\n*\{[\s\S]*?\}\n*```/g, "")
        .replace(/```\{[\s\S]*?\}\n*```/g, "")
        .trim();
    }
    return contentToDisplay;
  }, [rawContent, contentToDisplay, roleplayEvaluation]);

  return (
    <AIElementMessageContent className={className}>
      {filesList}
      <MarkdownContent
        content={displayContent}
        isLoading={isLoading}
        rehypePlugins={[...rehypePlugins, [rehypeKatex, { output: "html" }]]}
        className="my-3"
        components={components}
      />
    </AIElementMessageContent>
  );
}

/**
 * Get file extension and check helpers
 */
const getFileExt = (filename: string) =>
  filename.split(".").pop()?.toLowerCase() ?? "";

const FILE_TYPE_MAP: Record<string, string> = {
  json: "JSON",
  csv: "CSV",
  txt: "TXT",
  md: "Markdown",
  py: "Python",
  js: "JavaScript",
  ts: "TypeScript",
  tsx: "TSX",
  jsx: "JSX",
  html: "HTML",
  css: "CSS",
  xml: "XML",
  yaml: "YAML",
  yml: "YAML",
  pdf: "PDF",
  png: "PNG",
  jpg: "JPG",
  jpeg: "JPEG",
  gif: "GIF",
  svg: "SVG",
  zip: "ZIP",
  tar: "TAR",
  gz: "GZ",
};

const IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"];

function getFileTypeLabel(filename: string): string {
  const ext = getFileExt(filename);
  return FILE_TYPE_MAP[ext] ?? (ext.toUpperCase() || "FILE");
}

function isImageFile(filename: string): boolean {
  return IMAGE_EXTENSIONS.includes(getFileExt(filename));
}

/**
 * Format bytes to human-readable size string
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "—";
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

/**
 * List of files from additional_kwargs.files (with optional upload status)
 */
function RichFilesList({
  files,
  threadId,
}: {
  files: FileInMessage[];
  threadId: string;
}) {
  if (files.length === 0) return null;
  return (
    <div className="mb-2 flex flex-wrap justify-end gap-2">
      {files.map((file, index) => (
        <RichFileCard
          key={`${file.filename}-${index}`}
          file={file}
          threadId={threadId}
        />
      ))}
    </div>
  );
}

/**
 * Single file card that handles FileInMessage (supports uploading state)
 */
function RichFileCard({
  file,
  threadId,
}: {
  file: FileInMessage;
  threadId: string;
}) {
  const { t } = useI18n();
  const isUploading = file.status === "uploading";
  const isImage = isImageFile(file.filename);

  if (isUploading) {
    return (
      <div className="bg-background border-border/40 flex max-w-50 min-w-30 flex-col gap-1 rounded-lg border p-3 opacity-60 shadow-sm">
        <div className="flex items-start gap-2">
          <Loader2Icon className="text-muted-foreground mt-0.5 size-4 shrink-0 animate-spin" />
          <span
            className="text-foreground truncate text-sm font-medium"
            title={file.filename}
          >
            {file.filename}
          </span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <Badge
            variant="secondary"
            className="rounded px-1.5 py-0.5 text-[10px] font-normal"
          >
            {getFileTypeLabel(file.filename)}
          </Badge>
          <span className="text-muted-foreground text-[10px]">
            {t.uploads.uploading}
          </span>
        </div>
      </div>
    );
  }

  if (!file.path) return null;

  const fileUrl = resolveArtifactURL(file.path, threadId);

  if (isImage) {
    return (
      <a
        href={fileUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="group border-border/40 relative block overflow-hidden rounded-lg border"
      >
        <img
          src={fileUrl}
          alt={file.filename}
          className="h-32 w-auto max-w-60 object-cover transition-transform group-hover:scale-105"
        />
      </a>
    );
  }

  return (
    <div className="bg-background border-border/40 flex max-w-50 min-w-30 flex-col gap-1 rounded-lg border p-3 shadow-sm">
      <div className="flex items-start gap-2">
        <FileIcon className="text-muted-foreground mt-0.5 size-4 shrink-0" />
        <span
          className="text-foreground truncate text-sm font-medium"
          title={file.filename}
        >
          {file.filename}
        </span>
      </div>
      <div className="flex items-center justify-between gap-2">
        <Badge
          variant="secondary"
          className="rounded px-1.5 py-0.5 text-[10px] font-normal"
        >
          {getFileTypeLabel(file.filename)}
        </Badge>
        <span className="text-muted-foreground text-[10px]">
          {formatBytes(file.size)}
        </span>
      </div>
    </div>
  );
}

const MessageContent = memo(MessageContent_);
