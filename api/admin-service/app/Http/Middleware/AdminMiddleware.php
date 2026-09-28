<?php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AdminMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $role = $request->input('x_user_role', '');
        if ($role !== 'ADMIN') {
            return response()->json([
                'success' => false,
                'message' => 'Admin access required',
            ], 403);
        }
        return $next($request);
    }
}
