<?php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class GatewayJwtAuth
{
    public function handle(Request $request, Closure $next): Response
    {
        $userId = $request->header('X-User-Id');
        $userEmail = $request->header('X-User-Email');
        $userRole = $request->header('X-User-Role', 'PLAYER');

        if ($userId && $userEmail) {
            $request->merge([
                'x_user_id' => $userId,
                'x_user_email' => $userEmail,
                'x_user_role' => $userRole,
            ]);
            return $next($request);
        }

        $authHeader = $request->header('Authorization');
        if (!$authHeader || !str_starts_with($authHeader, 'Bearer ')) {
            return response()->json([
                'success' => false,
                'message' => 'Authentication required',
            ], 401);
        }

        $token = substr($authHeader, 7);
        $jwtSecret = env('JWT_ACCESS_SECRET', 'dev-jwt-secret');

        try {
            $parts = explode('.', $token);
            if (count($parts) !== 3) {
                throw new \Exception('Invalid token format');
            }
            $payload = json_decode(base64_decode($parts[1]), true);
            if (!$payload || !isset($payload['sub'])) {
                throw new \Exception('Invalid token payload');
            }
            $request->merge([
                'x_user_id' => $payload['sub'],
                'x_user_email' => $payload['email'] ?? '',
                'x_user_role' => $payload['role'] ?? 'PLAYER',
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Invalid or expired token',
            ], 401);
        }

        return $next($request);
    }
}
