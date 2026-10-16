import { type AgentIdentity, type AuthConfig, ToolPermissionRegistry, resolveKey } from './auth.js';

export type { AgentIdentity, AuthConfig } from './auth.js';
export { ToolPermission, ToolPermissionRegistry } from './auth.js';

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export type MCPToolHandler = (params: Record<string, unknown>) => Promise<unknown>;

interface RPCRequest {
  jsonrpc: string;
  id: string | number | null;
  method: string;
  params?: Record<string, unknown>;
}

interface RPCResponse {
  jsonrpc: string;
  id: string | number | null;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

/** Options for creating an MCPServer. */
export interface MCPServerOptions {
  /** API key auth configuration. When omitted, no auth is required. */
  authConfig?: AuthConfig;
  /** Permission registry. When omitted, no permission checks are performed. */
  permissions?: ToolPermissionRegistry;
}

/** MCP JSON-RPC 2.0 server for AI agent interaction. */
export class MCPServer {
  private readonly tools = new Map<string, MCPTool>();
  private readonly handlers = new Map<string, MCPToolHandler>();
  private readonly serverName: string;
  private readonly serverVersion: string;
  private readonly authConfig?: AuthConfig;
  private readonly permissions?: ToolPermissionRegistry;

  constructor(name: string, version: string, options?: MCPServerOptions) {
    this.serverName = name;
    this.serverVersion = version;
    this.authConfig = options?.authConfig;
    this.permissions = options?.permissions;
  }

  registerTool(tool: MCPTool, handler: MCPToolHandler): void {
    this.tools.set(tool.name, tool);
    this.handlers.set(tool.name, handler);
  }

  /**
   * Handle a JSON-RPC request without authentication.
   * Backward compatible — no auth checks are performed.
   */
  async handleRequest(reqBody: string): Promise<string> {
    return this.dispatch(reqBody, null);
  }

  /**
   * Handle a JSON-RPC request with optional authentication.
   * Extracts "Bearer <key>" from the authHeader, validates the key,
   * and checks permissions before tool dispatch.
   *
   * When no authConfig is set on the server, behaves identically to handleRequest.
   */
  async handleAuthenticatedRequest(reqBody: string, authHeader?: string): Promise<string> {
    let identity: AgentIdentity | null = null;

    if (this.authConfig) {
      if (!authHeader) {
        return this.errorResponse(null, -32603, 'Unauthorized: missing Authorization header');
      }

      const key = authHeader.replace(/^Bearer\s+/i, '');
      identity = resolveKey(this.authConfig, key);

      if (!identity) {
        return this.errorResponse(null, -32603, 'Unauthorized: invalid API key');
      }
    }

    return this.dispatch(reqBody, identity);
  }

  private async dispatch(reqBody: string, identity: AgentIdentity | null): Promise<string> {
    let req: RPCRequest;
    try {
      req = JSON.parse(reqBody);
    } catch {
      return this.errorResponse(null, -32700, 'Parse error');
    }

    switch (req.method) {
      case 'initialize':
        return this.successResponse(req.id, {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: this.serverName, version: this.serverVersion },
        });

      case 'tools/list':
        return this.successResponse(req.id, { tools: [...this.tools.values()] });

      case 'tools/call': {
        const params = req.params as { name: string; arguments?: Record<string, unknown> } | undefined;
        if (!params?.name) return this.errorResponse(req.id, -32602, 'Missing tool name');

        // Permission check
        if (this.permissions && identity) {
          if (!this.permissions.isAllowed(identity, params.name)) {
            return this.errorResponse(req.id, -32603,
              `Permission denied: role '${identity.role}' cannot access tool '${params.name}'`);
          }
        }

        const handler = this.handlers.get(params.name);
        if (!handler) return this.errorResponse(req.id, -32602, `Unknown tool: ${params.name}`);

        try {
          const result = await handler(params.arguments ?? {});
          return this.successResponse(req.id, {
            content: [{ type: 'text', text: JSON.stringify(result) }],
          });
        } catch (err) {
          return this.errorResponse(req.id, -32000, String(err));
        }
      }

      default:
        return this.errorResponse(req.id, -32601, `Method not found: ${req.method}`);
    }
  }

  private successResponse(id: string | number | null, result: unknown): string {
    const resp: RPCResponse = { jsonrpc: '2.0', id, result };
    return JSON.stringify(resp);
  }

  private errorResponse(id: string | number | null, code: number, message: string): string {
    const resp: RPCResponse = { jsonrpc: '2.0', id, error: { code, message } };
    return JSON.stringify(resp);
  }
}
