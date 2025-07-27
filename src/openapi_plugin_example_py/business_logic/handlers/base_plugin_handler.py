"""Base handler for plugin requests with command execution support."""
from typing import Type, TypeVar
from openapi_plugin_common import CommandBase, CommandInvoker, RequestHandlerBase
from ..options import ExamplePluginOptions

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')
TCommand = TypeVar('TCommand', bound=CommandBase)
TContext = TypeVar('TContext')


class BasePluginHandler(RequestHandlerBase[TRequest, TResponse]):
    """Base handler with command execution support."""
    
    def __init__(
        self,
        command_invoker_factory,
        plugin_options: ExamplePluginOptions,
        telemetry_service=None
    ):
        """Initialize the handler."""
        super().__init__(telemetry_service)
        self._command_invoker_factory = command_invoker_factory
        self._plugin_options = plugin_options
    
    async def execute_command_async(
        self,
        command_type: Type[TCommand],
        context: TContext
    ) -> None:
        """Execute a command with the proper invoker setup."""
        # Create and execute command directly using our custom factory
        print(f"BasePluginHandler: Creating command for {command_type}")
        print(f"BasePluginHandler: Command factory type: {type(self._command_invoker_factory)}")
        
        # Use our custom factory to create the command with all services injected
        command = self._command_invoker_factory.create(command_type)
        
        # Execute the command directly
        await command.execute_async(context, self._plugin_options, None)