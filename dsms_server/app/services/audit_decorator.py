import functools
import traceback
from typing import Optional, Callable
from uuid import UUID
from app.services.audit_log import audit_log_writer


def audit_log(operation_type: str, include_request: bool = False, include_response: bool = False):
    """审计日志装饰器
    
    自动记录函数调用的日志，支持成功/失败记录。
    
    Args:
        operation_type: 操作类型
        include_request: 是否记录请求参数
        include_response: 是否记录响应数据（注意：可能包含敏感信息）
    
    Usage:
        @audit_log("user_login")
        async def login(username: str, password: str):
            ...
        
        @audit_log("create_device", include_request=True)
        async def create_device(device_data: dict):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从 kwargs 中提取 user_id（通常由 require_auth 提供）
            user_id = kwargs.get('user_id') or kwargs.get('user', {}).get('user_id') if isinstance(kwargs.get('user'), dict) else None
            ip_addr = kwargs.get('ip_addr') or _get_client_ip(kwargs.get('request'))
            
            # 准备操作详情
            details_parts = []
            if include_request:
                # 排除敏感字段
                safe_kwargs = {k: v for k, v in kwargs.items() 
                              if k not in ('password', 'token', 'secret', 'user', 'request')}
                if safe_kwargs:
                    details_parts.append(f"params: {safe_kwargs}")
            
            operation_details = "; ".join(details_parts) if details_parts else None
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 记录成功日志
                if include_response and result:
                    response_str = str(result)[:500]  # 限制长度
                    details = f"{operation_details}; response: {response_str}" if operation_details else f"response: {response_str}"
                else:
                    details = operation_details
                
                if user_id:
                    audit_log_writer.write_success(
                        user_id=UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id,
                        operation_type=operation_type,
                        operation_details=details,
                        ip_addr=ip_addr
                    )
                
                return result
                
            except Exception as e:
                # 记录失败日志
                error_msg = f"{type(e).__name__}: {str(e)}"
                stack_trace = traceback.format_exc() if include_request else None
                full_error = f"{error_msg}; trace: {stack_trace}" if stack_trace else error_msg
                
                if user_id:
                    audit_log_writer.write_failure(
                        user_id=UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id,
                        operation_type=operation_type,
                        operation_details=operation_details,
                        ip_addr=ip_addr,
                        error_msg=full_error
                    )
                
                # 重新抛出异常，不影响原逻辑
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or kwargs.get('user', {}).get('user_id') if isinstance(kwargs.get('user'), dict) else None
            ip_addr = kwargs.get('ip_addr') or _get_client_ip(kwargs.get('request'))
            
            details_parts = []
            if include_request:
                safe_kwargs = {k: v for k, v in kwargs.items() 
                              if k not in ('password', 'token', 'secret', 'user', 'request')}
                if safe_kwargs:
                    details_parts.append(f"params: {safe_kwargs}")
            
            operation_details = "; ".join(details_parts) if details_parts else None
            
            try:
                result = func(*args, **kwargs)
                
                if include_response and result:
                    response_str = str(result)[:500]
                    details = f"{operation_details}; response: {response_str}" if operation_details else f"response: {response_str}"
                else:
                    details = operation_details
                
                if user_id:
                    audit_log_writer.write_success(
                        user_id=UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id,
                        operation_type=operation_type,
                        operation_details=details,
                        ip_addr=ip_addr
                    )
                
                return result
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                stack_trace = traceback.format_exc() if include_request else None
                full_error = f"{error_msg}; trace: {stack_trace}" if stack_trace else error_msg
                
                if user_id:
                    audit_log_writer.write_failure(
                        user_id=UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id,
                        operation_type=operation_type,
                        operation_details=operation_details,
                        ip_addr=ip_addr,
                        error_msg=full_error
                    )
                
                raise
        
        # 根据函数类型返回正确的装饰器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _get_client_ip(request) -> Optional[str]:
    """从请求对象中提取客户端IP"""
    if request is None:
        return None
    
    try:
        # 优先从 X-Forwarded-For 头获取（反向代理场景）
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # 其次从 X-Real-IP 头获取
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 最后从 client 对象的 host 获取
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    except Exception:
        return None


# 导入 asyncio 用于检查协程函数
import asyncio
