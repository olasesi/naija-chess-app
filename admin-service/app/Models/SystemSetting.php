<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class SystemSetting extends Model
{
    use HasUuids;

    protected $table = 'system_settings';

    protected $fillable = ['key', 'value', 'description', 'type'];

    public $incrementing = false;
    protected $keyType = 'string';
}
