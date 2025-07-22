from django.shortcuts import render, redirect
from django.http import Http404
from .models import Tool
from .forms import ToolForm

from canvasops.tracing import trace_function, add_metadata, add_event, tracer
from canvasops.db_tracing import trace_queryset, trace_create, trace_update, trace_delete

# Create your views here.

def tool_selection(request):
    # Handle missing LTI session gracefully
    context = {
        'canvas_user_id': request.session.get('canvas_user_id', 'Unknown'),
        'canvas_course_id': request.session.get('canvas_course_id', 'Unknown'),
        'canvas_roles': request.session.get('canvas_roles', []),
        'canvas_url': request.session.get('canvas_url', ''),
    }
    return render(request, 'tools/tool_selection.html', context)

@trace_function("tools.list_tools")
def tool_list(request):
    """List all available tools with tracing."""
    with tracer.span("tools.list_tools") as span:
        # Add request metadata
        add_metadata("user.id", request.user.id if request.user.is_authenticated else None, span)
        add_metadata("request.method", request.method, span)
        
        # Trace the queryset operation
        tools = Tool.objects.all()
        
        @trace_queryset(tools, "tools.fetch_all")
        def fetch_tools():
            return list(tools)
        
        tool_list = fetch_tools()
        
        # Add result metadata
        add_metadata("tools.count", len(tool_list), span)
        add_event("tools.listed", {
            "count": len(tool_list),
            "user_id": request.user.id if request.user.is_authenticated else None
        }, span)
        
        return render(request, 'tools/tool_list.html', {'tools': tool_list})

@trace_function("tools.create_tool")
def tool_create(request):
    """Create a new tool with tracing."""
    if request.method == 'POST':
        form = ToolForm(request.POST)
        if form.is_valid():
            with tracer.span("tools.create_tool") as span:
                add_metadata("user.id", request.user.id if request.user.is_authenticated else None, span)
                add_metadata("tool.name", form.cleaned_data.get('name'), span)
                
                @trace_create(Tool)
                def create_tool():
                    return form.save()
                
                tool = create_tool()
                
                add_metadata("tool.id", tool.id, span)
                add_event("tool.created", {
                    "tool_id": tool.id,
                    "tool_name": tool.name,
                    "user_id": request.user.id if request.user.is_authenticated else None
                }, span)
                
                return redirect('tool_detail', pk=tool.pk)
    else:
        form = ToolForm()
    
    return render(request, 'tools/tool_form.html', {'form': form})

@trace_function("tools.tool_detail")
def tool_detail(request, pk):
    """View tool details with tracing."""
    with tracer.span("tools.tool_detail") as span:
        add_metadata("tool.id", pk, span)
        add_metadata("user.id", request.user.id if request.user.is_authenticated else None, span)
        
        try:
            tool = Tool.objects.get(pk=pk)
            add_metadata("tool.name", tool.name, span)
            add_event("tool.viewed", {
                "tool_id": pk,
                "tool_name": tool.name,
                "user_id": request.user.id if request.user.is_authenticated else None
            }, span)
            
            return render(request, 'tools/tool_detail.html', {'tool': tool})
        except Tool.DoesNotExist:
            add_metadata("error.type", "ToolNotFound", span)
            add_event("tool.not_found", {"tool_id": pk}, span)
            raise Http404("Tool not found")

@trace_function("tools.tool_update")
def tool_update(request, pk):
    """Update a tool with tracing."""
    try:
        tool = Tool.objects.get(pk=pk)
    except Tool.DoesNotExist:
        with tracer.span("tools.tool_update.error") as span:
            add_metadata("error.type", "ToolNotFound", span)
            add_metadata("tool.id", pk, span)
            add_event("tool.update.not_found", {"tool_id": pk}, span)
        raise Http404("Tool not found")
    
    if request.method == 'POST':
        form = ToolForm(request.POST, instance=tool)
        if form.is_valid():
            with tracer.span("tools.tool_update") as span:
                add_metadata("tool.id", pk, span)
                add_metadata("user.id", request.user.id if request.user.is_authenticated else None, span)
                add_metadata("tool.name", form.cleaned_data.get('name'), span)
                
                @trace_update(Tool)
                def update_tool():
                    return form.save()
                
                updated_tool = update_tool()
                
                add_event("tool.updated", {
                    "tool_id": pk,
                    "tool_name": updated_tool.name,
                    "user_id": request.user.id if request.user.is_authenticated else None
                }, span)
                
                return redirect('tool_detail', pk=updated_tool.pk)
    else:
        form = ToolForm(instance=tool)
    
    return render(request, 'tools/tool_form.html', {'form': form})

@trace_function("tools.tool_delete")
def tool_delete(request, pk):
    """Delete a tool with tracing."""
    try:
        tool = Tool.objects.get(pk=pk)
    except Tool.DoesNotExist:
        with tracer.span("tools.tool_delete.error") as span:
            add_metadata("error.type", "ToolNotFound", span)
            add_metadata("tool.id", pk, span)
            add_event("tool.delete.not_found", {"tool_id": pk}, span)
        raise Http404("Tool not found")
    
    if request.method == 'POST':
        with tracer.span("tools.tool_delete") as span:
            add_metadata("tool.id", pk, span)
            add_metadata("tool.name", tool.name, span)
            add_metadata("user.id", request.user.id if request.user.is_authenticated else None, span)
            
            @trace_delete(Tool)
            def delete_tool():
                tool.delete()
            
            delete_tool()
            
            add_event("tool.deleted", {
                "tool_id": pk,
                "tool_name": tool.name,
                "user_id": request.user.id if request.user.is_authenticated else None
            }, span)
            
            return redirect('tool_list')
    
    return render(request, 'tools/tool_confirm_delete.html', {'tool': tool})
