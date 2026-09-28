<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class AdminAction extends Model
{
    use HasUuids;

    protected $table = 'admin_actions';

    protected $fillable = ['admin_id', 'action', 'resource_type', 'resource_id', 'details', 'ip_address'];

    public $incrementing = false;
    protected $keyType = 'string';

    protected function casts(): array
    {
        return ['details' => 'array'];
    }
}
