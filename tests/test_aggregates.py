import pytest
from kant import aggregates, events
from kant.eventstore import EventStream


class BankAccountCreated(events.Event):
    __empty_stream__ = True

    id = events.CUIDField(primary_key=True)
    owner = events.CharField()


class DepositPerformed(events.Event):
    amount = events.DecimalField()


class WithdrawalPerformed(events.Event):
    amount = events.DecimalField()


@pytest.mark.asyncio
async def test_aggregate_should_apply_one_event(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.id
            self.owner = event.owner
            self.balance = 0

    bank_account = BankAccount()
    bank_account_created = BankAccountCreated(
        id=123,
        owner='John Doe',
    )
    # act
    bank_account.dispatch(bank_account_created)
    # assert
    assert bank_account.version == -1
    assert bank_account.current_version == 0
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 0


@pytest.mark.asyncio
async def test_aggregate_should_apply_many_events(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    bank_account_created = BankAccountCreated(
        id=123,
        owner='John Doe',
    )
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.dispatch(bank_account_created)
    bank_account.dispatch(deposit_performed)
    # assert
    assert bank_account.version == -1
    assert bank_account.current_version == 1
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 20


@pytest.mark.asyncio
async def test_aggregate_should_apply_event_list(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    bank_account_created = BankAccountCreated(
        id=123,
        owner='John Doe',
    )
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.dispatch([bank_account_created, deposit_performed])
    # assert
    assert bank_account.version == -1
    assert bank_account.current_version == 1
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 20


@pytest.mark.asyncio
async def test_aggregate_should_load_events(dbsession):
    # arrange

    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        ),
        DepositPerformed(
            amount=20,
            version=1,
        ),
        DepositPerformed(
            amount=20,
            version=2,
        )
    ])
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    # assert
    assert bank_account.version == 2
    assert bank_account.current_version == 2
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 40


@pytest.mark.asyncio
async def test_aggregate_should_apply_event_after_load_events(dbsession):
    # arrange

    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    # assert
    assert bank_account.version == 0
    assert bank_account.current_version == 1
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 20


@pytest.mark.asyncio
async def test_aggregate_should_be_created_from_events(dbsession):
    # arrange

    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount.from_stream(events)
    bank_account.dispatch(deposit_performed)
    # assert
    assert bank_account.version == 0
    assert bank_account.current_version == 1
    assert bank_account.id == 123
    assert bank_account.owner == 'John Doe'
    assert bank_account.balance == 20


@pytest.mark.asyncio
async def test_aggregate_should_return_new_events(dbsession):
    # arrange

    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )

    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    result = list(bank_account.get_events())
    # assert
    assert len(result) == 1
    assert result[0].version == 1
    assert result[0].amount == 20


@pytest.mark.asyncio
async def test_aggregate_should_return_all_events(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    result = list(bank_account.all_events())
    # assert
    assert len(result) == 2
    assert result[0].version == 0
    assert result[0].id == 123
    assert result[0].owner == 'John Doe'
    assert result[1].version == 1
    assert result[1].amount == 20


@pytest.mark.asyncio
async def test_aggregate_should_return_stored_events(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    result = list(bank_account.stored_events())
    # assert
    assert len(result) == 1
    assert result[0].version == 0
    assert result[0].id == 123
    assert result[0].owner == 'John Doe'


@pytest.mark.asyncio
async def test_aggregate_should_decode_to_json(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.id
            self.owner = event.owner
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.amount

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    result = bank_account.json()
    # assert
    expected_result = '{"balance": 20, "id": 123, "owner": "John Doe"}'
    assert isinstance(result, str)
    assert result == expected_result


@pytest.mark.asyncio
async def test_aggregate_should_decode_to_json_filtering_by_fields(dbsession):
    # arrange
    class BankAccount(aggregates.Aggregate):
        id = aggregates.IntegerField()
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.id
            self.owner = event.owner
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.amount

    events = EventStream([
        BankAccountCreated(
            id=123,
            owner='John Doe',
            version=0,
        )
    ])
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.fetch_events(events)
    bank_account.dispatch(deposit_performed)
    result = bank_account.json(only=('id',))
    # assert
    expected_result = '{"id": 123}'
    assert isinstance(result, str)
    assert result == expected_result


@pytest.mark.asyncio
async def test_aggregate_should_save_to_eventstore(dbsession, eventsourcing):
    # arrange
    class BankAccount(aggregates.Aggregate):
        __keyspace__ = 'event_store'
        id = aggregates.IntegerField(primary_key=True)
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    bank_account_created = BankAccountCreated(
        id=123,
        owner='John Doe',
    )
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.dispatch([bank_account_created, deposit_performed])
    await bank_account.save()
    async with eventsourcing.open('event_store') as eventstore:
        stored_events = await eventstore.get_stream(bank_account.id)
        stored_bank_account = BankAccount.from_stream(stored_events)
    # assert
    assert stored_bank_account.version == 1
    assert stored_bank_account.current_version == 1
    assert stored_bank_account.id == 123
    assert stored_bank_account.owner == 'John Doe'
    assert stored_bank_account.balance == 20


@pytest.mark.asyncio
async def test_manager_should_get_aggregate(dbsession, eventsourcing):
    # arrange
    class BankAccount(aggregates.Aggregate):
        __keyspace__ = 'event_store'
        id = aggregates.IntegerField(primary_key=True)
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    bank_account_created = BankAccountCreated(
        id=123,
        owner='John Doe',
    )
    deposit_performed = DepositPerformed(
        amount=20,
    )
    # act
    bank_account = BankAccount()
    bank_account.dispatch([bank_account_created, deposit_performed])
    async with eventsourcing.open('event_store') as eventstore:
        await eventstore.append_to_stream(bank_account.id, bank_account.get_events())
    stored_bank_account = await BankAccount.objects.get(bank_account_created.id)
    # assert
    assert stored_bank_account.version == 1
    assert stored_bank_account.current_version == 1
    assert stored_bank_account.id == 123
    assert stored_bank_account.owner == 'John Doe'
    assert stored_bank_account.balance == 20


@pytest.mark.asyncio
async def test_manager_aggregate_should_find_all_aggregates(dbsession, eventsourcing):
    # arrange
    class BankAccount(aggregates.Aggregate):
        __keyspace__ = 'event_store'
        id = aggregates.IntegerField(primary_key=True)
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    # act
    bank_account_1 = BankAccount()
    bank_account_1.dispatch([BankAccountCreated(
        id=123,
        owner='John Doe',
    ), DepositPerformed(
        amount=20,
    )])
    await bank_account_1.save()
    bank_account_2 = BankAccount()
    bank_account_2.dispatch([BankAccountCreated(
        id=456,
        owner='John Doe',
    ), DepositPerformed(
        amount=20,
    ), DepositPerformed(
        amount=20,
    )])
    await bank_account_2.save()
    stored_aggregates = []
    async for aggregate in BankAccount.objects.all():
        stored_aggregates.append(aggregate)
    # assert
    assert stored_aggregates[0].version == 1
    assert stored_aggregates[0].current_version == 1
    assert stored_aggregates[0].id == 123
    assert stored_aggregates[0].owner == 'John Doe'
    assert stored_aggregates[0].balance == 20
    assert stored_aggregates[1].version == 2
    assert stored_aggregates[1].current_version == 2
    assert stored_aggregates[1].id == 456
    assert stored_aggregates[1].owner == 'John Doe'
    assert stored_aggregates[1].balance == 40


@pytest.mark.asyncio
async def test_aggregate_should_refresh_from_db(dbsession, eventsourcing):
    # arrange
    class BankAccount(aggregates.Aggregate):
        __keyspace__ = 'event_store'
        id = aggregates.IntegerField(primary_key=True)
        owner = aggregates.CharField()
        balance = aggregates.IntegerField()

        def apply_bank_account_created(self, event):
            self.id = event.get('id')
            self.owner = event.get('owner')
            self.balance = 0

        def apply_deposit_performed(self, event):
            self.balance += event.get('amount')

    # act
    bank_account = BankAccount()
    bank_account.dispatch([BankAccountCreated(
        id=123,
        owner='John Doe',
    ), DepositPerformed(
        amount=20,
    )])
    await bank_account.save()
    stored_bank_account_1 = await BankAccount.objects.get(bank_account.id)
    stored_bank_account_2 = await BankAccount.objects.get(bank_account.id)
    stored_bank_account_1.dispatch(DepositPerformed(
        amount=20,
    ))
    await stored_bank_account_1.save()
    await stored_bank_account_2.refresh_from_db()
    # assert
    assert stored_bank_account_2.version == 2
    assert stored_bank_account_2.current_version == 2
    assert stored_bank_account_2.id == 123
    assert stored_bank_account_2.owner == 'John Doe'
    assert stored_bank_account_2.balance == 40
