import * as vscode from 'vscode';
import { exec } from 'child_process';

interface SourceSpan {
  start_line: number;
  start_col: number;
  end_line: number;
  end_col: number;
}

interface SiplDiagnostic {
  severity: 'error' | 'warning';
  code: string;
  message: string;
  span: SourceSpan | null;
}

interface CliResponse {
  ok: boolean;
  command: string;
  diagnostics: SiplDiagnostic[];
  result: unknown;
}

export function activate(context: vscode.ExtensionContext): void {
  const diagnosticCollection = vscode.languages.createDiagnosticCollection('sipl');
  const outputChannel = vscode.window.createOutputChannel('SIPL');

  const runCli = async (subcommand: 'check' | 'run'): Promise<void> => {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'sipl') {
      vscode.window.showWarningMessage('Open a .sipl file first.');
      return;
    }

    await editor.document.save();
    const filePath = editor.document.uri.fsPath;
    const config = vscode.workspace.getConfiguration('sipl');
    const exe = config.get<string>('executablePath', 'sipl');

    const cmd = `${exe} ${subcommand} "${filePath}" --json`;

    exec(cmd, (error, stdout, stderr) => {
      diagnosticCollection.clear();

      if (!stdout.trim()) {
        outputChannel.appendLine(`[SIPL Error] Failed to execute '${cmd}': ${stderr || error?.message}`);
        outputChannel.show(true);
        vscode.window.showErrorMessage(`SIPL CLI execution failed. Check Output -> SIPL.`);
        return;
      }

      let response: CliResponse;
      try {
        response = JSON.parse(stdout) as CliResponse;
      } catch {
        outputChannel.appendLine(`[SIPL Error] Invalid JSON output:\n${stdout}`);
        outputChannel.show(true);
        return;
      }

      if (!response.ok) {
        const vsDiagnostics: vscode.Diagnostic[] = response.diagnostics.map((d) => {
          const startLine = Math.max(0, (d.span?.start_line ?? 1) - 1);
          const startCol = Math.max(0, (d.span?.start_col ?? 1) - 1);
          const endLine = Math.max(startLine, (d.span?.end_line ?? startLine + 1) - 1);
          const endCol = Math.max(startCol + 1, (d.span?.end_col ?? startCol + 1) - 1);

          const range = new vscode.Range(startLine, startCol, endLine, endCol);
          const diag = new vscode.Diagnostic(range, `[${d.code}] ${d.message}`, vscode.DiagnosticSeverity.Error);
          diag.source = 'sipl';
          return diag;
        });

        diagnosticCollection.set(editor.document.uri, vsDiagnostics);
        outputChannel.appendLine(`[${subcommand.toUpperCase()} FAILED] ${filePath}`);
        response.diagnostics.forEach((d) => outputChannel.appendLine(`  [${d.code}] ${d.message}`));
        outputChannel.show(true);
        return;
      }

      outputChannel.appendLine(`[${subcommand.toUpperCase()} OK] ${filePath}`);
      outputChannel.appendLine(JSON.stringify(response.result, null, 2));
      outputChannel.show(true);
      vscode.window.showInformationMessage(`SIPL ${subcommand}: OK`);
    });
  };

  context.subscriptions.push(
    diagnosticCollection,
    outputChannel,
    vscode.commands.registerCommand('sipl.check', () => runCli('check')),
    vscode.commands.registerCommand('sipl.run', () => runCli('run'))
  );
}

export function deactivate(): void {}
